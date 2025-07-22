import re
from typing import Dict, Optional
from datetime import datetime

VENDOR_PATTERNS = [
    r"^[A-Z0-9 &.,'-]{5,}$",  
    r"\bSDN BHD\b",        
    r"\b(?:Reliance Jio|Jio|Airtel|BSNL|Vodafone Idea|VI|ACT Fibernet|Hathway|Spectra|Tata Power|MSEB|BESCOM|UPPCL|Walmart|Target|Amazon|Costco|Best Buy|Aldi|Lidl|Tesco|Sainsbury|Carrefour|Auchan|Edeka|Rewe|Inc\\.|LLC|Ltd\\.|Corporation|Corp\\.|Supermarket|Market|Store)\b",
    r"[A-Za-z ]+Inc\\.|[A-Za-z ]+LLC", 
    r"\b(?:Pvt\.\s?Ltd\.|Pvt Ltd|Private Limited|Ltd\.|LLP|PLC|Limited|Co\.\s?Ltd\.|Company)\b",
    r"[A-Za-z ]+(?:Pvt\.\s?Ltd|LLP|Ltd\.|Private Limited|PLC)"
]
DATE_PATTERNS = [
    r"\b\d{2}[/-]\d{2}[/-]\d{4}\b",  
    r"\b\d{4}[/-]\d{2}[/-]\d{2}\b",  
    r"\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]* \d{1,2}, \d{4}\b",
    # 20 Apr 2024 or 20 April 2024
    r"\b\d{1,2}[ -](?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec)[a-z]*[ -]\d{4}\b",
    # Apr 20 2024 or April 20 2024
    r"\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec)[a-z]*[ -]\d{1,2}[ ,-]\d{4}\b"
]
AMOUNT_PATTERNS = [
    # Label followed by amount (handles Total, Amount Payable etc.)
    r"(?i)(?:total(?: amount)?|amount(?: due| payable| paid)?|balance|grand total|sum)[^\d]{0,15}(\d[\d,]*(?:[\.,]\d{2})?)",
    # Currency symbol before amount
    r"(?i)(?:₹\s*|rs\.?\s*)(\d[\d,]*(?:[\.,]\d{2})?)",
    # Currency symbol after amount
    r"(?i)(\d[\d,]*(?:[\.,]\d{2})?)\s*(?:₹|rs\.?)"
]
CURRENCY_PATTERNS = [r"(\$|USD|EUR|€|£|RM|₹|INR|Rs\.?)"]

VENDOR_CATEGORY_MAP = {
    "Walmart": "Groceries",
    "Target": "Retail",
    "Amazon": "Online Shopping",
    "Comcast": "Internet",
    "Costco": "Wholesale",
    "Tesco": "Groceries",
    "Aldi": "Groceries",
    "Lidl": "Groceries",
    "Sainsbury": "Groceries",
    "Carrefour": "Groceries",
    "Auchan": "Groceries",
    "Edeka": "Groceries",
    "Rewe": "Groceries",
    "Reliance Jio": "Internet",
    "Jio": "Internet",
    "Airtel": "Internet",
    "BSNL": "Internet",
    "Vodafone Idea": "Internet",
    "VI": "Internet",
    "ACT Fibernet": "Internet",
    "Hathway": "Internet",
    "Spectra": "Internet",
    "Tata Power": "Electricity",
    "MSEB": "Electricity",
    "BESCOM": "Electricity",
    "UPPCL": "Electricity",
    "KSEB": "Electricity",
    "Adani Electricity": "Electricity",
    "MSEDCL": "Electricity",
    "MSEDCL": "Electricity",
    "Maharashtra State Electricity": "Electricity",
    "CESC": "Electricity",
    "TPDDL": "Electricity",
    "TNEB": "Electricity",
    "UPCL": "Electricity",
    "JVVNL": "Electricity",
    "DHBVN": "Electricity",
    "Dakshin Haryana Bijli Vitran Nigam": "Electricity",
    "DAKSHIN HARYANA BIJLI VITRAN NIGAM": "Electricity",
    "UHBVN": "Electricity",
    "APSPDCL": "Electricity",
    "BSES": "Electricity",
    "PGVCL": "Electricity",
    "PSPCL": "Electricity",
    "CSPDCL": "Electricity",
    "KPTCL": "Electricity",
    "BESL": "Electricity"
}

def extract_vendor(text: str) -> Optional[str]:
   
    for pattern in VENDOR_PATTERNS:
        match = re.search(pattern, text, re.MULTILINE)
        if match:
            return match.group(0).strip()
   
    for line in text.splitlines():
        if line.strip() and line.strip().isupper() and len(line.strip()) > 5:
            return line.strip()
    return "Unknown"

def extract_date(text: str) -> Optional[str]:
    for pattern in DATE_PATTERNS:
        match = re.search(pattern, text)
        if match:
            return match.group(0)
    return None

def extract_amount(text: str) -> Optional[float]:
    for pattern in AMOUNT_PATTERNS:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            try:
                return float(match.group(1).replace(',', '').replace(' ', ''))
            except (ValueError, IndexError):
                continue
    return None

def extract_currency(text: str) -> Optional[str]:
    for pattern in CURRENCY_PATTERNS:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(1).upper().strip()
    return None

def extract_category(vendor: Optional[str]) -> Optional[str]:
    if vendor:
        vend_low = vendor.lower()
        import re as _re
        for v, cat in VENDOR_CATEGORY_MAP.items():
            pattern = rf"\b{_re.escape(v.lower())}\b"
            if _re.search(pattern, vend_low):
                return cat
      
        if any(k in vend_low for k in ("electricity", "power", "bijli", "discom")):
            return "Electricity"
        if any(k in vend_low for k in ("internet", "broadband", "fibernet")):
            return "Internet"
    return "Other"

def extract_line_items(text: str):
    items = []
    pattern = re.compile(r"([A-Za-z0-9 \-]+)\s+(\d+[\.,]\d{2})")
    for line in text.splitlines():
        match = pattern.search(line)
        if match:
            item = match.group(1).strip()
            price = float(match.group(2).replace(',', '.'))
            items.append({'item': item, 'price': price})
    return items

def parse_receipt_text(text: str) -> Dict:
    vendor = extract_vendor(text)
    date_str = extract_date(text)
    amount = extract_amount(text)
    currency = extract_currency(text)
    category = extract_category(vendor)
   
    date = None
    if date_str:
        for fmt in (
            "%d-%m-%Y",
            "%d/%m/%Y",
            "%m/%d/%Y",
            "%Y-%m-%d",
            "%B %d, %Y",
            "%b %d, %Y",
            "%d %b %Y",
            "%d %B %Y",
            "%d-%b-%Y",
            "%d-%B-%Y",
            "%b %d %Y",
            "%B %d %Y",
        ):
            try:
                date = datetime.strptime(date_str, fmt).date()
                break
            except ValueError:
                continue
    return {
        "vendor": vendor or "Unknown",
        "date": date,
        "amount": amount,
        "category": category,
        "currency": currency
    } 