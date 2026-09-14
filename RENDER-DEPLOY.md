# GEORUSH — Render Cloud API Deployment

## Goal
Run the FastAPI crawler on a cloud server so the marketing team does not need Python or your PC.

## 1. Push this repository to GitHub
Push the GEORUSH files, including `render.yaml`, `requirements.txt`, and `main.py`.

## 2. Create the Render service
In Render, create a new **Web Service** and connect the `PharmaQA-ops/GEORUSH-SEO` GitHub repository.

Render settings:
- Runtime: Python
- Build Command: `pip install -r requirements.txt`
- Start Command: `uvicorn main:app --host 0.0.0.0 --port $PORT`
- Health Check Path: `/api/health`

`render.yaml` in this repository contains the same settings for Blueprint deployment.

## 3. Test the cloud API
After deployment, open:

`https://YOUR-RENDER-SERVICE.onrender.com/api/health`

Expected response:

```json
{"status":"ok","service":"georush-seo-api","version":"0.14.0"}
```

## 4. Connect GitHub Pages to Render
Edit `api-config.js`:

```js
window.GEORUSH_API = "https://YOUR-RENDER-SERVICE.onrender.com";
```

Commit and push that change. GitHub Pages will then call the cloud API.

## 5. Marketing team workflow
They only open the GEORUSH GitHub Pages URL, enter a site, and click **Run audit**. No Python, PowerShell, Uvicorn, or local server is required on their computers.
