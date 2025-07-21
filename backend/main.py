from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import os
from .utils import validate_file

app = FastAPI()

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
    validate_file(file)
    filename = os.path.join(UPLOAD_DIR, file.filename)
    with open(filename, "wb") as f:
        content = await file.read()
        f.write(content)
    return JSONResponse({"filename": file.filename, "message": "File uploaded successfully."}) 