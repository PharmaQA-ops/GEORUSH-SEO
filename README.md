# GEORUSH SEO
Step 9 — Analytics + working sidebar navigation.

Flat architecture.

Analytics foundation:
- 28-day analytics summary
- Sessions/users/conversions placeholders for GA4
- GSC clicks/impressions/CTR/position compatibility
- `/api/analytics/summary`
- GA4 environment-variable placeholders

Navigation fix:
- Sidebar items are clickable
- Dashboard, Keywords, Rankings, Competitors, Site Audit, Content, Backlinks and Analytics use in-page sections/hash navigation
- Active navigation state
- Browser back/forward support
- No separate HTML pages required

Important:
GA4 sessions/users/conversions are not fabricated. They remain zero until the Google Analytics Data API/OAuth connection is configured.

Run:
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
