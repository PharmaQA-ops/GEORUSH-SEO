# GEORUSH SEO — Step 32 Production Intelligence

This version fixes the non-clickable navigation, search and backend syntax.

Frontend:
- Root index.html
- Real button-based sidebar navigation
- Working Dashboard / Keywords / Rankings / Competitors / Site Audit / Content / Backlinks / Analytics
- Working search button and Enter key
- Working Run Audit button

Backend:
- Correct FastAPI main.py
- `/api/health`
- `/api/crawl`
- `/api/search`
- `/api/ai/ask`
- GSC, keyword, competitor, content and analytics endpoints

Run locally:
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8000

Then open the root index.html with Live Server.

GitHub Pages:
The frontend works there, but live crawling requires the Python API to be deployed separately.


## GEORUSH Cloud API (Render)

This repository is prepared for a cloud-hosted FastAPI crawler. GitHub Pages serves the frontend; Render runs `main.py` and the crawler.

1. Create a Render Web Service from this GitHub repository.
2. Use build command: `pip install -r requirements.txt`.
3. Use start command: `uvicorn main:app --host 0.0.0.0 --port $PORT`.
4. After deployment, open `/api/health` on the Render URL.
5. Put the Render URL into `api-config.js` as `window.GEORUSH_API`.
6. Commit and push the frontend change to GitHub Pages.

The marketing team only needs the GitHub Pages URL; they do not need Python or this local API setup.

See `RENDER-DEPLOY.md` for the exact cloud deployment sequence.


## Step 27 — Local Ollama AI
GEORUSH can run its three AI research agents locally through Ollama. No Gemini/OpenRouter/Groq API key is required. Default test model: `qwen3:1.7b`. See `STEP27.txt`.

## Step 28 — One-click Windows operation
GEORUSH now automatically starts/reuses Ollama, verifies the configured model, starts the local API, and opens the desktop UI. Users do not need to run PowerShell commands every day. See STEP28.txt.


## Step 29 - Async Deep Research
Deep Research now runs as a background job. The browser starts a job and polls its status, so long Ollama runs do not hit a frontend HTTP timeout.

New endpoints: POST /api/research/multi-agent/start and GET /api/research/multi-agent/status/{job_id}.


### Step 31 — Ultra Low-RAM Ollama
Default local model is qwen3:0.6b with compact context/output settings for 4 GB RAM test machines.


## Step 32
Production intelligence layer: evidence-based keyword intelligence, title-aware competitor discovery, validated 3-agent Ollama outputs, live research stages, and Run Ollama AI controls.
