# GEORUSH SEO v1.0.0

Internal Marketing SEO Intelligence Platform.

## Release

Production Marketing Release 1.0.0.

## Start

-   Windows desktop: `GEORUSH-SEO-START.vbs`
-   Setup: `INSTALL-GEORUSH.bat`
-   Build source EXE: `BUILD-GEORUSH.bat`

## Core modules

Dashboard, Keywords, Rankings, Competitors, Site Audit, Content,
Backlinks, Analytics and Reports.

## Local AI

GEORUSH uses local Ollama for AI analysis and 3-agent Deep Research.
Default model: `qwen3:0.6b`.

GEORUSH owns the Ollama lifecycle: stop pre-existing Ollama processes at
startup, start Ollama on demand, and stop the managed runtime on
shutdown.

## Reporting

The report preview is the source for Print / Save PDF. Completed 3-agent
research is included in the report and HTML export.

## Analytics

GA4 is included as a controlled backend integration path. GSC remains
the source for real search query/ranking evidence.

## Branding

The supplied GEORUSH logo is included as `georush-logo.png` and
`georush.ico`. The startup screen uses a GEORUSH-branded animated
progress/reveal inspired by the motion language observed on the NeoLeaf
reference site.

Reference reviewed: https://neoleaf.bytetown.agency/

## Deployment documents

See the included user manual, administrator deployment guide, Ollama
operations guide, GA4/GSC connector guide, technical architecture,
security checklist and UAT workbook.

## Repository rule

Deploy only from `PharmaQA-ops/GEORUSH-SEO`. Do not upload this release
to `ggl-main-dashboard`.

## Security

Do not commit API tokens, passwords, service-account JSON files or
production `.env` files.

## Windows build
For a Windows EXE/installer, use the included GitHub Actions workflow or run `BUILD-GEORUSH.bat` on Windows. The build script now detects and recreates broken `.venv` environments and bootstraps pip before installing PyInstaller.

## Branding
The `branding/` directory contains the complete GEORUSH logo asset pack generated from the supplied owner artwork.
