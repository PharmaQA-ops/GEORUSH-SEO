# GEORUSH SEO --- Marketing User Manual v1.0.0

## 1. Start GEORUSH

Use the GEORUSH desktop shortcut or approved launcher. Do not start
Ollama manually first.

GEORUSH will: 1. stop pre-existing Ollama desktop/server processes; 2.
start its own API; 3. start Ollama only when an audit or AI function
requires it; 4. open the GEORUSH interface.

## 2. Run a Site Audit

1.  Open Dashboard.
2.  Enter the target website.
3.  Click **Run audit**.
4.  Wait for crawl completion.
5.  Review SEO score, pages, issues and technical results.

The crawler checks observable page signals. It does not claim traffic,
backlinks, rankings or search volume unless a connected data source
provides those values.

## 3. Keyword Intelligence

Open **Keywords** and click **Run Keyword Intelligence** after an audit.
For real query performance, import a Google Search Console export or
connect the approved GSC workflow.

## 4. Competitors

Open **Competitors**. - Inspect a known competitor manually, or - use
**Auto-discover competitors**.

GEORUSH extracts observable page signals including title, headings, word
count, links, response time and HTTPS. Local Ollama can interpret the
evidence during Deep Research.

## 5. Reports

Open **Reports**. 1. Generate the report. 2. Run **3-Agent Deep
Research** when required. 3. Confirm the AI section is visible in the
report preview. 4. Click **Print / Save PDF**.

The PDF should include the audit plus the latest stored 3-agent
research.

## 6. Local AI

Use **Run Ollama AI** for a single local AI analysis or **3-Agent Deep
Research** for: - competitor research; - SEO / keyword research; -
critical review and synthesis.

The local model is not a cloud API. Internet access is still required
when GEORUSH collects public web evidence.

## 7. Analytics

Open **Analytics**. - Crawler analytics work immediately after an
audit. - GA4 shows connection status. - When the backend connector is
configured, use **Load GA4 Report**.

## 8. Sign out / close

Use the GEORUSH sign-out/close workflow. GEORUSH owns the Ollama process
and stops its local Ollama runtime during shutdown.

## 9. Do not

-   Do not share `.env` files or service-account credentials.
-   Do not expose the local API to the public Internet.
-   Do not manually edit production crawl results.
-   Do not interpret evidence-based keyword themes as guaranteed
    rankings.
