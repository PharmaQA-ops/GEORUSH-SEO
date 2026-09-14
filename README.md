# GEORUSH SEO

Step 3 — Technical SEO Engine.

Flat repository architecture:
- index.html
- styles.css
- app.js
- main.py
- crawler.py
- requirements.txt

Technical checks include:
- HTTP errors
- missing/long titles
- duplicate titles
- missing/long descriptions
- duplicate descriptions
- H1 structure
- canonical consistency
- noindex
- thin content
- image ALT
- mixed content
- redirects
- orphan pages
- page depth
- severity classification
- technical health score

Run locally:
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8000

API health:
http://127.0.0.1:8000/api/health
