# GEORUSH SEO
Step 7 — Competitor Intelligence.

Flat architecture.

New module:
- competitor.py

Capabilities:
- Competitor domain inspection
- HTTP status and response time
- Title and meta description signals
- H1 count
- Word count
- Internal/external link counts
- Target-vs-competitor comparison foundation
- Up to 10 competitor URLs per comparison

Endpoints:
POST /api/competitor/inspect
POST /api/competitor/compare

This step intentionally does not fabricate competitor keyword rankings, traffic, backlinks, domain authority, or search volume. Those require external data providers/APIs.

Run:
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
