from pydantic import BaseModel, Field
from typing import Optional
from datetime import date

class ReceiptMeta(BaseModel):
    id: Optional[int]
    filename: str
    upload_date: date

class Transaction(BaseModel):
    id: Optional[int]
    receipt_id: int
    vendor: str
    date: date
    amount: float
    category: str
    currency: Optional[str] = Field(default=None, description="Currency symbol or code, e.g., $, EUR") 