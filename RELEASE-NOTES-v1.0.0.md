# GEORUSH SEO v1.0.0 --- Marketing Release

## Release status

Production release candidate for the Marketing / SEO team.

## Included

-   GEORUSH SEO Command Center
-   Site Audit and technical crawler
-   SEO score and issue prioritization
-   Keyword Intelligence
-   Competitor Intelligence and automatic competitor discovery
-   Competitor page title extraction
-   Content Intelligence
-   Backlink / link-signal analysis
-   Rankings module prepared for Google Search Console
-   Analytics module with Google Analytics 4 connection path
-   Management-ready HTML/PDF reporting
-   GEORUSH AI using local Ollama
-   Three-agent local Deep Research
-   Ollama competitor intelligence
-   Evidence-based keyword intelligence
-   GEORUSH-owned Ollama lifecycle
-   Windows one-click desktop launcher
-   Startup loading animation and GEORUSH branding
-   Security and deployment documentation

## Version

GEORUSH SEO: 1.0.0 Local AI model default: qwen3:0.6b Default local
Ollama runtime: CPU AVX2 on the low-spec workstation

## Release rule

This release must be deployed only from the `PharmaQA-ops/GEORUSH-SEO`
repository. Do not upload these files to `ggl-main-dashboard`.

## Known limitations

-   Google rankings, search volume and CPC are not fabricated. They
    require GSC or an approved keyword-data provider.
-   GA4 requires backend credentials and property access before live
    data is returned.
-   Local Ollama quality and speed depend on workstation CPU/RAM/GPU.
-   GitHub Pages hosts the frontend only; the Python API must run
    locally or on an approved backend.
