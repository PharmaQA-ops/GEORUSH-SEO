# GEORUSH SEO
Step 6 — Keyword Intelligence.

Flat architecture:
- index.html
- styles.css
- app.js
- main.py
- crawler.py
- score.py
- gsc.py
- keywords.py
- requirements.txt

Keyword intelligence includes:
- GSC keyword/page normalization
- Search clicks, impressions, CTR and position
- Search intent classification
- Informational / Commercial / Transactional / Navigational intent
- Opportunity scoring
- Opportunity ranking
- Intent distribution
- Keyword-to-page mapping foundation

Endpoint:
POST /api/keywords/analyze

This step deliberately does not invent search volume, keyword difficulty or CPC. Those require a real keyword-data provider and can be connected later.

Run:
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
