from fastapi import FastAPI, UploadFile, File, HTTPException, Query
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import os
from .utils import validate_file
from .ocr import extract_text
from .parser import parse_receipt_text, extract_line_items
# fix missing import for category classification
from .parser import extract_category
from datetime import date
from .db import SessionLocal, Receipt, Transaction, LineItem
from typing import List, Optional
from sqlalchemy import func
from collections import Counter
import statistics
from datetime import datetime
from .models import Transaction as TransactionModel, FileUploadModel
from .algorithms import (
    linear_search, hash_search, range_search, pattern_search,
    timsort, quicksort, compute_aggregates, frequency_distribution,
    monthly_aggregation, sliding_window_aggregation
)

app = FastAPI()

# Fix categories for existing records on startup
@app.on_event("startup")
def recategorize_existing():
    db = SessionLocal()
    try:
        transactions = db.query(Transaction).all()
        updated = False
        for t in transactions:
            new_cat = extract_category(t.vendor)
            if new_cat != t.category:
                t.category = new_cat
                updated = True
        if updated:
            db.commit()
    finally:
        db.close()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_DIR = "../data/uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@app.post("/upload/")
async def upload_receipt(file: UploadFile = File(...)):
  
    try:
        file.file.seek(0, os.SEEK_END)
        size = file.file.tell()
        file.file.seek(0)
    except Exception as e:
        return JSONResponse(status_code=400, content={"detail": f"File validation failed: {str(e)}"})
    # Existing validation
    try:
        validate_file(file)
    except HTTPException as e:
        return JSONResponse(status_code=e.status_code, content={"detail": str(e.detail)})
    except Exception as e:
        return JSONResponse(status_code=400, content={"detail": f"Unexpected file validation error: {str(e)}"})

    filename = os.path.join(UPLOAD_DIR, file.filename)
    try:
        content = await file.read()
        with open(filename, "wb") as f:
            f.write(content)
    except Exception as e:
        return JSONResponse(status_code=500, content={"detail": f"Failed to save file: {str(e)}"})

    ext = os.path.splitext(file.filename)[1].lower()
    try:
        text = extract_text(content, ext)
    except Exception as e:
        return JSONResponse(status_code=500, content={"detail": f"Failed to extract text: {str(e)}"})
    if not text:
        return JSONResponse(status_code=400, content={"detail": "Could not extract text from file."})

    try:
        parsed = parse_receipt_text(text)
    except Exception as e:
        return JSONResponse(status_code=500, content={"detail": f"Failed to parse receipt: {str(e)}"})

    # Check for required fields
    required_fields = ["vendor", "date", "amount", "category"]
    for k in required_fields:
        if not parsed.get(k):
            if k in ("date", "amount"):
                parsed[k] = None
            else:
                parsed[k] = "N/A"

   
    try:
        validated = TransactionModel(
            id=None,
            receipt_id=0,
            vendor=parsed["vendor"],
            date=parsed["date"],
            amount=parsed["amount"],
            category=parsed["category"],
            currency=parsed.get("currency")
        )
    except Exception as e:
        validated = None

    db = SessionLocal()
    try:
        receipt = Receipt(filename=file.filename, upload_date=date.today())
        db.add(receipt)
        db.commit()
        db.refresh(receipt)
        transaction = Transaction(
            receipt_id=receipt.id,
            vendor=parsed["vendor"],
            date=parsed["date"],
            amount=parsed["amount"],
            category=parsed["category"],
            currency=parsed.get("currency")
        )
        db.add(transaction)
        db.commit()
        db.refresh(transaction)
       
        line_items = extract_line_items(text)
        for li in line_items:
            db.add(LineItem(transaction_id=transaction.id, item=li['item'], price=li['price']))
        db.commit()
       
        if parsed.get("date") and hasattr(parsed["date"], "isoformat"):
            parsed["date"] = parsed["date"].isoformat()

        response_data = {
            "filename": file.filename,
            "receipt_id": receipt.id,
            "transaction_id": transaction.id,
            "message": "File uploaded, parsed, and stored successfully (some fields may be missing).",
            "extracted": parsed,
            "line_items": line_items
        }
    except Exception as e:
        db.rollback()
        return JSONResponse(status_code=500, content={"detail": f"Database error: {str(e)}"})
    finally:
        db.close()
    return JSONResponse(response_data)

@app.get("/transactions/")
def get_transactions(
    vendor: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    keyword: Optional[str] = Query(None),
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
    amount_min: Optional[float] = Query(None),
    amount_max: Optional[float] = Query(None),
):
    db = SessionLocal()
    try:
        query = db.query(Transaction)
        results = query.all()
       
        data = [
            {
                "id": t.id,
                "receipt_id": t.receipt_id,
                "vendor": t.vendor,
                "date": t.date,
                "amount": t.amount,
                "category": t.category,
                "currency": t.currency
            }
            for t in results
        ]
       
        if vendor:
            data = linear_search(data, vendor, ["vendor"])
        if category:
            data = linear_search(data, category, ["category"])
        if keyword:
            data = linear_search(data, keyword, ["vendor", "category"])
        if date_from:
            data = [t for t in data if t["date"] and str(t["date"]) >= date_from]
        if date_to:
            data = [t for t in data if t["date"] and str(t["date"]) <= date_to]
        if amount_min is not None:
            data = [t for t in data if t["amount"] is not None and t["amount"] >= amount_min]
        if amount_max is not None:
            data = [t for t in data if t["amount"] is not None and t["amount"] <= amount_max]
       
        for t in data:
            if t["date"]:
                t["date"] = t["date"].isoformat()
        return {"transactions": data}
    except Exception as e:
        return JSONResponse(status_code=500, content={"detail": f"Failed to fetch transactions: {str(e)}"})
    finally:
        db.close()


@app.get("/transactions/sorted/")
def get_sorted_transactions(
    sort_by: str = Query("date", regex="^(date|amount)$"),
    order: str = Query("desc", regex="^(asc|desc)$"),
    vendor: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    keyword: Optional[str] = Query(None),
):
    db = SessionLocal()
    try:
        query = db.query(Transaction)
        results = query.all()
        data = [
            {
                "id": t.id,
                "receipt_id": t.receipt_id,
                "vendor": t.vendor,
                "date": t.date,
                "amount": t.amount,
                "category": t.category,
                "currency": t.currency
            }
            for t in results
        ]
    
        if vendor:
            data = linear_search(data, vendor, ["vendor"])
        if category:
            data = linear_search(data, category, ["category"])
        if keyword:
            data = linear_search(data, keyword, ["vendor", "category"])
      
        reverse = order == "desc"
       
        data = timsort(data, sort_by, reverse=reverse)
        for t in data:
            if t["date"]:
                t["date"] = t["date"].isoformat()
        return {"transactions": data}
    except Exception as e:
        return JSONResponse(status_code=500, content={"detail": f"Failed to fetch sorted transactions: {str(e)}"})
    finally:
        db.close()

@app.get("/transactions/stats/")
def get_transaction_stats(
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    vendor: Optional[str] = Query(None),
    keyword: Optional[str] = Query(None),
):
    db = SessionLocal()
    try:
        query = db.query(Transaction)
        results = query.all()
        data = [
            {
                "id": t.id,
                "receipt_id": t.receipt_id,
                "vendor": t.vendor,
                "date": t.date,
                "amount": t.amount,
                "category": t.category,
                "currency": t.currency
            }
            for t in results
        ]
       
        if vendor:
            data = linear_search(data, vendor, ["vendor"])
        if category:
            data = linear_search(data, category, ["category"])
        if keyword:
            data = linear_search(data, keyword, ["vendor", "category"])
        # Aggregation
        amounts = [t["amount"] for t in data if t["amount"] is not None]
        stats = compute_aggregates(data, "amount")
        stats["count"] = len(amounts)
        stats["vendor_frequency"] = frequency_distribution(data, "vendor")
        stats["category_frequency"] = frequency_distribution(data, "category")
        # Only transactions with date for monthly aggregation
        monthly = monthly_aggregation([t for t in data if t["date"] is not None], "date", "amount")
        stats["monthly_totals"] = monthly
        stats["monthly_moving_avg"] = sliding_window_aggregation(dict(sorted(monthly.items())), window=3) if monthly else {}
        return stats
    except Exception as e:
        return JSONResponse(status_code=500, content={"detail": f"Failed to fetch transaction stats: {str(e)}"})
    finally:
        db.close()

@app.get("/transactions/{transaction_id}/items/")
def get_line_items(transaction_id: int):
    db = SessionLocal()
    try:
        items = db.query(LineItem).filter(LineItem.transaction_id == transaction_id).all()
        return [{"item": i.item, "price": i.price} for i in items]
    finally:
        db.close()
# Manual trigger to recategorize all transactions
@app.post("/maintenance/recategorize/")
def recategorize_transactions():
    db = SessionLocal()
    try:
        transactions = db.query(Transaction).all()
        updated = 0
        for t in transactions:
            new_cat = extract_category(t.vendor)
            if new_cat != t.category:
                t.category = new_cat
                updated += 1
        if updated:
            db.commit()
        return {"updated": updated}
    finally:
        db.close() 