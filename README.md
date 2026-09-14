# GEORUSH SEO
Step 5 — Google Search Console foundation.

Flat architecture:
- index.html
- styles.css
- app.js
- main.py
- crawler.py
- score.py
- gsc.py
- requirements.txt

GSC capabilities:
- Search clicks
- Impressions
- CTR
- Average position
- Query/page dimensions
- Date range
- Up to 25,000 rows per request
- OAuth access-token-ready API

Endpoints:
GET /api/health
POST /api/crawl
GET /api/gsc/demo
POST /api/gsc/search-analytics

Security:
Never commit Google client secrets, access tokens, or refresh tokens to GitHub. Use environment variables or a secure backend credential store.

Run locally:
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
