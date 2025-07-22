from pydantic import BaseModel, Field, field_validator
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
    date: Optional[date] = None
    amount: Optional[float] = None
    category: str
    currency: Optional[str] = Field(default=None, description="Currency symbol or code, e.g., $, EUR")

class FileUploadModel(BaseModel):
    filename: str
    content_type: str
    size: int

    @field_validator('filename')
    @classmethod
    def check_extension(cls, v):
        allowed = {'.jpg', '.jpeg', '.png', '.pdf', '.txt'}
        ext = v.lower().rsplit('.', 1)[-1] if '.' in v else ''
        if f'.{ext}' not in allowed:
            raise ValueError(f'Unsupported file type: .{ext}')
        return v

    @field_validator('size')
    @classmethod
    def check_size(cls, v):
        if v > 10 * 1024 * 1024:
            raise ValueError('File size exceeds 10 MB limit.')
        return v 