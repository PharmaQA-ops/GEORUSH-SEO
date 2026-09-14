GEORUSH SEO v17 — SELF-CONTAINED DESKTOP APP

This is the version requested for a true desktop backup.

The EXE itself contains:
- GEORUSH FastAPI API
- GEORUSH crawler
- SEO scoring
- search
- module logic
- GEORUSH web interface

It does NOT depend on Render or the GitHub Pages site to perform audits.
The EXE starts the GEORUSH API internally and opens the dashboard inside the app.

Marketing user:
1. Install GEORUSH SEO once.
2. Double-click the GEORUSH SEO desktop icon.
3. Enter a website.
4. Click Run Audit.

No Python, VS Code, PowerShell, Uvicorn, or browser is required after installation.

Internet is still required to crawl external websites.

Windows installer is built automatically by GitHub Actions:
Actions -> Build GEORUSH Self-Contained Windows App -> Run workflow.

The installer includes a normal Windows uninstaller.
