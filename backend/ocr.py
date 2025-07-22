import pytesseract
from PIL import Image, ImageFilter
import pdfplumber
import io
from typing import Optional
pytesseract.pytesseract.tesseract_cmd = r"C:\\Program Files\\Tesseract-OCR\\tesseract.exe"

def preprocess_image(image: Image.Image) -> Image.Image:
  
    image = image.convert('L')
   
    image = image.point(lambda x: 0 if x < 140 else 255, '1')
   
    image = image.filter(ImageFilter.SHARPEN)
    return image

def extract_text_from_image(file_bytes: bytes) -> str:
    image = Image.open(io.BytesIO(file_bytes))
    image = preprocess_image(image)
    try:
        text = pytesseract.image_to_string(image)
    except Exception as e:
        raise RuntimeError(f"Tesseract OCR failed: {e}")
    return text

def extract_text_from_pdf(file_bytes: bytes) -> str:
    text = ""
    with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if not page_text:
                pil_img = page.to_image(resolution=300).original
                pil_img = preprocess_image(pil_img)
                try:
                    page_text = pytesseract.image_to_string(pil_img)
                except Exception as e:
                    raise RuntimeError(f"Tesseract OCR failed on PDF page: {e}")
            text += page_text or ""
    return text

def extract_text(file_bytes: bytes, file_ext: str) -> Optional[str]:
    if file_ext in ['.jpg', '.jpeg', '.png']:
        return extract_text_from_image(file_bytes)
    elif file_ext == '.pdf':
        return extract_text_from_pdf(file_bytes)
    elif file_ext == '.txt':
        return file_bytes.decode(errors='ignore')
    else:
        return None 