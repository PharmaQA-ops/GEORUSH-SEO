
def build_ai_context(crawl=None, keywords=None, competitors=None, radar=None):
    crawl=crawl or {}; keywords=keywords or []; competitors=competitors or []; radar=radar or {}
    score=(crawl.get("seo_score") or {}).get("total", crawl.get("health", 0))
    return {"score":score,"issues":crawl.get("issues",0),"pages":crawl.get("pages",0),
            "keyword_opportunities":len(keywords),"competitors":len(competitors),"radar":radar}

def generate_insights(context):
    score=float(context.get("score",0) or 0); issues=int(context.get("issues",0) or 0)
    pages=int(context.get("pages",0) or 0); insights=[]
    if score < 60: insights.append("Technical SEO needs immediate attention before scaling content or rankings.")
    elif score < 80: insights.append("The site has a workable foundation, but technical issues are limiting SEO efficiency.")
    else: insights.append("The technical foundation is relatively healthy; focus on ranking and content opportunities.")
    if issues: insights.append(f"Prioritize the highest-severity issues across the {pages} crawled pages.")
    if context.get("keyword_opportunities",0): insights.append("Review high-opportunity GSC queries with strong impressions and positions that can move onto page one.")
    if context.get("competitors",0): insights.append("Compare title, H1, content depth, technical hygiene and page speed signals against the automatically discovered competitors.")
    radar=context.get("radar") or {}
    if radar.get("malicious") is True: insights.append("Cloudflare URL Scanner reported a malicious verdict; investigate before publishing this report externally.")
    return {"summary":insights[0],"insights":insights,"mode":"GEORUSH AI rules engine"}

def generate_report_recommendations(crawl=None, competitors=None, keywords=None, radar=None):
    crawl=crawl or {}; competitors=competitors or []; keywords=keywords or []; radar=radar or {}
    results=crawl.get("results",[]) or []
    issues={}
    for p in results:
        for i in p.get("issues",[]) or []: issues[i]=issues.get(i,0)+1
    rec=[]
    if issues.get("HTTP_ERROR",0) or issues.get("CRAWL_ERROR",0):
        rec.append({"priority":"Critical","area":"Crawlability","action":"Resolve HTTP/crawl failures before expanding content or link acquisition."})
    for key,label in [("MISSING_CANONICAL","Indexation"),("DUPLICATE_TITLE","On-page SEO"),("MISSING_DESCRIPTION","On-page SEO"),("MISSING_IMAGE_ALT","Accessibility"),("THIN_CONTENT","Content"),("MULTIPLE_H1","On-page SEO")]:
        if issues.get(key):
            rec.append({"priority":"High","area":label,"action":f"Address {key.replace('_',' ').title()} on {issues[key]} affected page(s)."})
    if keywords:
        rec.append({"priority":"High","area":"Keywords","action":"Create or improve landing pages for high-impression, low-CTR and page-two queries."})
    if competitors:
        top=competitors[0]
        rec.append({"priority":"Medium","area":"Competitors","action":f"Benchmark against {top.get('url','the top discovered competitor')} and close measurable content and technical gaps."})
    if radar.get("configured"):
        rec.append({"priority":"Medium","area":"Web Security & Performance","action":"Review Cloudflare URL Scanner findings, request chains, technologies, TLS and security verdicts."})
    return rec

def ask(question, context=None):
    q=question.lower(); context=context or {}
    if "competitor" in q: return {"summary":"Use the automatic competitor set to compare technical and content signals.","insights":["Review the top discovered domains.","Compare title, description, H1, content depth, internal links and response time.","Use the gap analysis to prioritize pages and content."],"mode":"GEORUSH AI rules engine"}
    if "radar" in q or "cloudflare" in q: return {"summary":"Use Cloudflare Radar URL Scanner as a supplementary security, network and technology signal.","insights":["Review redirects and request chains.","Check technologies and TLS/certificate signals.","Review security verdicts and suspicious requests."],"mode":"GEORUSH AI rules engine"}
    if "score" in q: return generate_insights(context)
    if "keyword" in q or "ranking" in q: return {"summary":"Prioritize queries with strong impressions and weak CTR or position.","insights":["Filter GSC queries by opportunity score.","Map each priority query to one primary landing page."],"mode":"GEORUSH AI rules engine"}
    if "technical" in q or "audit" in q: return {"summary":"Start with Critical and High severity technical issues.","insights":["Fix HTTP/crawl failures first.","Resolve indexability and canonical conflicts.","Then address on-page and content issues."],"mode":"GEORUSH AI rules engine"}
    return {"summary":"GEORUSH AI is ready to analyze your connected SEO datasets.","insights":["Run a site audit.","Connect Google Search Console.","Run automatic competitor discovery.","Run the Cloudflare Radar scan when credentials are configured."],"mode":"GEORUSH AI rules engine"}
