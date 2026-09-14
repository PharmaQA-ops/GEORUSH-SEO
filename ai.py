def build_ai_context(crawl=None, keywords=None, competitors=None):
    crawl=crawl or {}; keywords=keywords or []; competitors=competitors or []
    score=(crawl.get("seo_score") or {}).get("total", crawl.get("health", 0))
    return {"score":score,"issues":crawl.get("issues",0),"pages":crawl.get("pages",0),
            "keyword_opportunities":len(keywords),"competitors":len(competitors)}

def generate_insights(context):
    score=float(context.get("score",0) or 0); issues=int(context.get("issues",0) or 0)
    pages=int(context.get("pages",0) or 0); insights=[]
    if score < 60: insights.append("Technical SEO needs immediate attention before scaling content or rankings.")
    elif score < 80: insights.append("The site has a workable foundation, but technical issues are limiting SEO efficiency.")
    else: insights.append("The technical foundation is relatively healthy; focus on ranking and content opportunities.")
    if issues: insights.append(f"Prioritize the highest-severity issues across the {pages} crawled pages.")
    if context.get("keyword_opportunities",0): insights.append("Review high-opportunity GSC queries with positions in the page-one/page-two range.")
    return {"summary":insights[0],"insights":insights,"mode":"GEORUSH AI rules engine"}

def ask(question, context=None):
    q=question.lower(); context=context or {}
    if "score" in q: return generate_insights(context)
    if "keyword" in q or "ranking" in q:
        return {"summary":"Prioritize queries with strong impressions and weak CTR or position.",
                "insights":["Filter GSC queries by opportunity score.","Map each priority query to one primary landing page."],
                "mode":"GEORUSH AI rules engine"}
    if "technical" in q or "audit" in q:
        return {"summary":"Start with Critical and High severity technical issues.",
                "insights":["Fix HTTP/crawl failures first.","Resolve indexability and canonical conflicts.","Then address on-page and content issues."],
                "mode":"GEORUSH AI rules engine"}
    return {"summary":"GEORUSH AI is ready to analyze your connected SEO datasets.",
            "insights":["Run a site audit.","Connect Google Search Console.","Connect analytics data.","Then ask a focused SEO question."],
            "mode":"GEORUSH AI rules engine"}
