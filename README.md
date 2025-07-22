# IntellijAnalyzer

A lightweight tool that turns unstructured receipt and bill images/PDFs into meaningful insights.  Upload a file, the system extracts text with OCR, classifies the transaction, stores it, and presents trends on a friendly dashboard.

---

## 1. Quick-start

1. **Clone and enter the project**  
   ```bash
   git clone <repo-url>
   cd IntellijAnalyzer
   ```
2. **Create a virtual environment**  
   ```bash
   python -m venv .venv
   .venv\Scripts\activate   # Windows
   # source .venv/bin/activate  # macOS / Linux
   ```
3. **Install dependencies**  
   ```bash
   pip install -r backend/requirements.txt
   pip install streamlit altair pandas requests
   ```
4. **Install Tesseract-OCR** (required for text extraction).  
   - Windows: grab the installer from https://github.com/tesseract-ocr/tesseract  
   - macOS: `brew install tesseract`  
   - Linux: `sudo apt install tesseract-ocr`
   
   Make sure the binary is discoverable.  On Windows, set an env variable:
   ```powershell
   setx TESSDATA_PREFIX "C:\Program Files\Tesseract-OCR"
   ```
5. **Run the backend**  
   ```bash
   uvicorn backend.main:app --reload --port 9000
   ```
6. **Launch the dashboard**  
   In another shell (same venv):
   ```bash
   streamlit run frontend/app.py
   ```
   Visit http://localhost:8501 to play with the UI.

---

## 2. Architecture & Design Choices

| Layer | Tech | Purpose |
|-------|------|---------|
| **Frontend** | Streamlit | Rapid, pythonic dashboard for non-technical users |
| **API** | FastAPI | Async endpoints for upload, query, and analytics |
| **OCR** | `pytesseract` + Tesseract | Converts images/PDFs to raw text |
| **Parser** | Regex-based heuristics | Extracts vendor, date, amount, currency, category |
| **DB** | SQLite via SQLAlchemy | Zero-config persistence; data lives in `data/intellijanalyzer.db` |

Why this stack?
* Wanted a single-language solution––Python all the way.
* FastAPI offers swagger docs and async file uploads out-of-the-box.
* Streamlit makes charts trivial and keeps dev velocity high.
* SQLite keeps deployment simple; swap for Postgres in prod.

### Data Journey

1. **Upload** – User drops a receipt PDF/JPG in the UI → POST `/upload/`.
2. **OCR** – Backend converts to text; multi-page PDFs are handled page-by-page.
3. **Parsing** – Regexes find key fields; category is guessed from a vendor→category map.
4. **Persistence** – Receipt, transaction, and line-item rows are recorded in SQLite.
5. **Analytics** – Aggregations run in memory and are streamed to the UI as JSON.

---

## 3. Typical User Journeys

* **Expense Tracker** – Bulk-upload monthly bills, then filter by vendor to see spend.
* **Budget Audit** – Sort transactions by amount to spot unusually high charges.
* **Trend Watch** – Review the time-series chart to catch rising utility costs.

---

## 4. Limitations

* OCR accuracy depends on document quality and the underlying Tesseract model.
* Vendor detection uses simple regex patterns—new merchants may be missed.
* SQLite and in-memory analytics work for thousands, not millions, of records.
* Security hardening (auth, rate-limits, validation) is minimal—run behind a firewall.
* No automated tests yet;

---

## 5. Assumptions

* PDFs/JPGs are below 10 MB; larger files risk time-outs.
* Dates appear in common international formats (DD/MM/YYYY, YYYY-MM-DD, etc.).
* Indian ISPs and electricity boards cover the majority of regional utility bills; the list is not exhaustive.
* Deployment is on a single machine. horizontal scaling wasn’t a requirement.

