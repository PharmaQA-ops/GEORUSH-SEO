# GEORUSH SEO — Step 10
AI Intelligence + complete navigation/search fix.

Step 10 adds:
- GEORUSH AI rules engine
- `/api/ai/ask`
- Robust delegated sidebar navigation
- Dashboard / Keywords / Rankings / Competitors / Site Audit / Content / Backlinks / Analytics
- Hash navigation and browser back/forward
- Search fallback against latest crawl
- UI remains navigable when the API is offline

Important:
GitHub Pages runs the frontend only. Python crawler/API must run locally or on a separate backend host.

Local:
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
