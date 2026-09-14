# GEORUSH SEO
Step 4 — GEORUSH SEO Score.

Flat architecture. The crawl now produces a weighted 0–100 SEO score:
Technical SEO 30%, Indexability 20%, On-Page SEO 20%, Content Quality 15%, Internal Linking 10%, Performance 5%.

Score grades:
90–100 Excellent
80–89 Good
70–79 Needs Improvement
50–69 Poor
0–49 Critical

Run:
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
