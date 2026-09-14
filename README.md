# GEORUSH SEO
Step 8 — Content Intelligence + Search Fix.

Flat architecture:
- index.html
- styles.css
- app.js
- main.py
- crawler.py
- score.py
- gsc.py
- keywords.py
- competitor.py
- content.py
- requirements.txt

Step 8:
- Content analysis
- Word count
- Unique word count
- Top terms
- Keyword occurrence/density
- Content issue detection
- Content API

Search fix:
- Global frontend search
- Search across crawled URL/title/description/H1
- Search API
- Enter-to-search
- Table filtering
- Search index populated by latest crawl
- Works with dynamic crawl results

Endpoints:
POST /api/search
POST /api/content/analyze

Run:
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
