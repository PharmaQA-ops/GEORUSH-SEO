# GEORUSH SEO --- Administrator Deployment Guide v1.0.0

## Repository

Production source repository: `PharmaQA-ops/GEORUSH-SEO`

## Architecture

Frontend: static HTML/CSS/JS. Backend: Python FastAPI. Local AI: Ollama.
Desktop shell: pywebview / Windows launcher. Reporting: browser print
engine plus HTML export. Optional analytics: GA4 Data API. Optional
search data: Google Search Console.

## Windows deployment

1.  Install Python 3.11+ on the approved workstation.
2.  Install Ollama once.
3.  Verify the required local model can be downloaded.
4.  Extract the GEORUSH release package to a controlled directory.
5.  Run `INSTALL-GEORUSH.bat`.
6.  Run `CREATE-GEORUSH-SHORTCUT.vbs`.
7.  Launch GEORUSH from the shortcut.

## Local API

Default: `http://127.0.0.1:8000`

Ollama: `http://127.0.0.1:11434`

The API should remain bound to loopback unless an approved deployment
requires another network topology.

## Ollama lifecycle

GEORUSH first stops existing Ollama desktop/server processes. It then
starts its own Ollama server only when required. The default low-spec
runtime uses `OLLAMA_LLM_LIBRARY=cpu_avx2`.

## Environment

Use `env.example` as the template. Never commit production secrets.

Important variables include: - `OLLAMA_MODEL` - `OLLAMA_LLM_LIBRARY` -
`OLLAMA_PORT` - `GA4_PROPERTY_ID` - `GOOGLE_APPLICATION_CREDENTIALS`

## Production backend

For a shared team deployment, run the FastAPI backend on an approved
internal server or Render/private service. GitHub Pages alone cannot
execute the Python backend.

## GitHub Pages

The Pages site is suitable for the frontend/static interface. Configure
`api-config.js` to point to an approved backend when using a remote
deployment.

## Rollback

Keep the previous tagged release ZIP and commit SHA. To roll back,
deploy the previous release package or restore the previous approved Git
tag. Do not force-push production history.

## Security

-   Loopback-only Ollama by default.
-   Do not expose Ollama directly to the Internet.
-   Protect GA4 service-account credentials.
-   Restrict backend CORS in a shared production deployment.
-   Review `SECURITY.md` before external deployment.
