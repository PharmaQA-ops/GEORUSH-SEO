# GEORUSH SEO --- Technical Architecture v1.0.0

``` text
Windows Marketing Workstation
        |
        +-- GEORUSH Desktop Launcher
        |       |
        |       +-- FastAPI :8000
        |       |
        |       +-- Ollama :11434 (on demand)
        |
        +-- Browser / pywebview UI
                |
                +-- Audit / Crawler
                +-- Keyword Intelligence
                +-- Competitor Intelligence
                +-- Content Intelligence
                +-- Reports
                +-- GA4 connector
                +-- GSC connector
                +-- Local Ollama agents
```

## Three-agent research

Agent 1: Competitor Researcher. Agent 2: SEO / Keyword Researcher. Agent
3: Critical Reviewer and Report Synthesizer.

The agents use the same local Ollama runtime and public evidence
gathered by GEORUSH.

## Evidence policy

GEORUSH must distinguish: - directly observed crawl facts; - public
search evidence; - connected GSC/GA4 data; - local-model interpretation.

The system must not invent search volume, CPC, rankings, traffic,
backlink counts or revenue.

## Reporting

The report preview is the source for browser Print / Save PDF. The
current Deep Research result is stored in application state and rendered
into the report before printing.
