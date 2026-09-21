"""GEORUSH 3-agent local deep research pipeline."""
import json, re, time
from urllib.parse import urlparse
import httpx
from bs4 import BeautifulSoup
from ollama_agent import run_agent, OllamaAgentError, OLLAMA_MODEL


def _search(query, limit=8):
    try:
        r=httpx.get("https://html.duckduckgo.com/html/",params={"q":query},headers={"User-Agent":"GEORUSH-Research/1.0"},timeout=15,follow_redirects=True)
        r.raise_for_status(); soup=BeautifulSoup(r.text,"html.parser")
        out=[]
        for x in soup.select(".result")[:limit]:
            a=x.select_one(".result__a"); sn=x.select_one(".result__snippet")
            if a: out.append({"title":a.get_text(" ",strip=True),"url":a.get("href",""),"snippet":sn.get_text(" ",strip=True) if sn else ""})
        return out
    except Exception as e:
        return [{"error":str(e),"query":query}]


def _fetch(url, max_chars=2500):
    try:
        if not re.match(r"^https?://",url): url="https://"+url
        r=httpx.get(url,headers={"User-Agent":"Mozilla/5.0 (compatible; GEORUSH-Research/1.0)"},timeout=20,follow_redirects=True)
        soup=BeautifulSoup(r.text,"html.parser")
        for t in soup(["script","style","noscript","svg"]): t.decompose()
        title=soup.title.get_text(" ",strip=True) if soup.title else ""
        h1=[x.get_text(" ",strip=True) for x in soup.find_all("h1")]
        h2=[x.get_text(" ",strip=True) for x in soup.find_all("h2")]
        text=" ".join(soup.stripped_strings)
        return {"url":url,"final_url":str(r.url),"status":r.status_code,"title":title,
                "h1":h1[:8],"h2":h2[:10],"text":text[:max_chars]}
    except Exception as e: return {"url":url,"error":str(e)}


def _clean_json(value, default):
    if isinstance(value,dict) and "raw" in value and len(value)==1:
        raw=value.get("raw","")
        if isinstance(raw,str):
            try:
                parsed=json.loads(raw)
                if isinstance(parsed,dict): return parsed
            except Exception: pass
    return value if isinstance(value,dict) else default


def _agent1_fallback(pack):
    comps=pack.get("competitor_analysis",{}).get("competitors",[])
    rows=[]
    for c in comps[:5]:
        s=c.get("signals",{})
        rows.append({"domain":c.get("domain") or c.get("url",""),"why_relevant":"Discovered from topic-aligned public search evidence.",
                     "site_title":s.get("title",""),"observed_signals":{"words":s.get("word_count",0),"h1":s.get("h1",[]),"canonical":s.get("canonical",False),"https":s.get("https",False)},
                     "gaps":["Requires deeper page/keyword comparison for definitive gap analysis."],"evidence_level":"Observed public page signals"})
    return {"summary":f"GEORUSH identified {len(rows)} topic-relevant competitor domain(s) from public search evidence.","competitors":rows,
            "opportunities":["Compare competitor service pages and topic coverage against the target.","Build content around validated competitor topic themes."],
            "sources":[x.get("url") for x in pack.get("search_results",[]) if x.get("url")][:8]}


def _agent2_fallback(pack):
    pages=pack.get("pages",[]); h=[]
    for p in pages:
        h.extend(p.get("h1",[])[:8]); h.extend(p.get("h2",[])[:8])
    themes=[]
    for x in h:
        x=str(x).strip()
        if x and x.lower() not in [z.lower() for z in themes]: themes.append(x)
    return {"summary":"Keyword intelligence is derived from target headings, page titles and public search-result evidence; no search-volume claim is made.",
            "keyword_themes":[{"keyword":x,"intent":"Commercial" if any(k in x.lower() for k in ["logistics","service","cargo","freight"]) else "Informational","evidence":"Target page heading/title"} for x in themes[:15]],
            "content_gaps":["Expand thin topic pages where the audit identifies low word counts.","Create dedicated pages for validated service/topic themes."],
            "seo_opportunities":["Align title/H1/topic intent on priority pages.","Use internal links to connect related service and capability pages."],
            "cautions":["Actual Google rankings, search volume and CPC require GSC or a SERP/keyword provider."],
            "sources":[x.get("url") for x in pack.get("search_results",[]) if x.get("url")][:8]}


def _agent3_fallback(pack, agent1, agent2):
    comps=agent1.get("competitors",[])
    top=comps[0].get("domain") if comps else None
    findings=[]
    target=pack.get("target_profile",{})
    if target.get("title"): findings.append({"priority":"High","finding":f"Target title: {target['title']}","recommendation":"Use the title as the baseline for topic and search-intent alignment."})
    if target.get("word_count",0)<300: findings.append({"priority":"High","finding":"Target page has thin content by GEORUSH crawl criteria.","recommendation":"Expand useful, unique content while preserving the primary search intent."})
    return {"executive_summary":f"Research completed using public web evidence and local Ollama analysis. {len(comps)} competitor domain(s) were identified for comparison." if comps else "Research completed, but no sufficiently relevant competitor domain was established from the collected evidence.",
            "confidence":"Medium — evidence is primarily public search results and observable page signals.","top_competitor":top or "Not established from available evidence",
            "critical_findings":findings,"opportunities":agent2.get("seo_opportunities",[])+agent1.get("opportunities",[]),
            "action_plan":[{"timeframe":"Immediate","actions":["Resolve critical crawl errors identified by the audit.","Review priority title, description, canonical and content issues."]},{"timeframe":"Next 30 days","actions":["Build content around validated keyword/topic themes.","Benchmark selected competitor pages and internal-link structures."]}],
            "limitations":["No search-volume, CPC or Google ranking data was claimed without GSC/provider evidence."],
            "sources":list(dict.fromkeys(agent1.get("sources",[])+agent2.get("sources",[])))[:12]}


def build_research_pack(target, keywords=None, competitor_limit=5, progress_callback=None):
    from competitor import discover_competitors, analyze_competitor_set
    keywords=[str(x).strip() for x in (keywords or []) if str(x).strip()]
    if progress_callback: progress_callback(8,"Building target profile")
    discovery=discover_competitors(target, keywords, competitor_limit)
    if progress_callback: progress_callback(18,"Discovering relevant competitor domains")
    comps=[x.get("url") for x in discovery.get("competitors",[]) if x.get("url")]
    analysis=analyze_competitor_set(target,comps,discovery.get("target_profile"))
    if progress_callback: progress_callback(24,f"Inspecting {len(comps)} competitor domain(s)")
    urls=[target]+comps[:competitor_limit]
    pages=[_fetch(u,2500) for u in urls]
    search_results=[]
    title=discovery.get("site_title","")
    query_terms=discovery.get("query_terms",[])
    queries=[]
    for q in keywords[:4]+query_terms[:5]+([title] if title else []):
        if q and q not in queries: queries.append(q)
    for q in queries[:6]: search_results.extend(_search(q,5))
    profile=discovery.get("target_profile",{}).get("signals",{})
    return {"target":target,"site_title":title or profile.get("title","") or (pages[0].get("title","") if pages else ""),
            "target_profile":profile,"keywords":keywords[:10],"query_terms":query_terms[:10],
            "search_results":search_results[:12],"competitors":analysis,"pages":pages,
            "generated_at":time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime())}


def run_multi_research(target, keywords=None, competitor_limit=5, progress_callback=None):
    pack=build_research_pack(target,keywords,competitor_limit,progress_callback)
    if progress_callback: progress_callback(32,"Agent 1 — Competitor Research")
    try:
        agent1=run_agent("""You are GEORUSH Agent 1, the COMPETITOR RESEARCHER. Return JSON only. Use the supplied evidence. Identify relevant competitor domains and observable site signals. Compare titles, headings, content depth, service/topic coverage and technical signals. Never invent traffic, rankings, revenue or backlinks. Schema: {summary:string, competitors:[{domain,why_relevant,site_title,observed_signals,gaps}], opportunities:[string], sources:[string]}.""",pack)
        agent1=_clean_json(agent1,{})
        if not agent1.get("competitors") and pack.get("competitors",{}).get("competitors"): agent1=_agent1_fallback(pack)
    except OllamaAgentError:
        raise
    if progress_callback: progress_callback(55,"Agent 1 completed · Agent 2 — SEO & Keyword Research")
    try:
        agent2=run_agent("""You are GEORUSH Agent 2, the SEO & KEYWORD RESEARCHER. Return JSON only. Use target titles/headings, public search results and page evidence. Produce evidence-based keyword themes and search-intent opportunities; do not invent search volume, CPC, rankings or traffic. Schema: {summary:string, keyword_themes:[{keyword,intent,evidence}], content_gaps:[string], seo_opportunities:[string], cautions:[string], sources:[string]}.""",pack,{"competitor_agent":agent1})
        agent2=_clean_json(agent2,{})
        if not agent2.get("keyword_themes") and not agent2.get("content_gaps"): agent2=_agent2_fallback(pack)
    except OllamaAgentError:
        raise
    if progress_callback: progress_callback(78,"Agent 2 completed · Agent 3 — Critical Review")
    try:
        agent3=run_agent("""You are GEORUSH Agent 3, the CRITICAL REVIEWER and REPORT SYNTHESIZER. Return JSON only. Cross-check Agent 1 and Agent 2 against the evidence. Do not repeat raw JSON. Do not invent rankings, market share, traffic, backlinks or revenue. If a top competitor cannot be established, say so. Schema: {executive_summary:string, confidence:string, top_competitor:string, critical_findings:[{priority,finding,recommendation}], opportunities:[string], action_plan:[{timeframe,actions:[string]}], limitations:[string], sources:[string]}.""",pack,{"competitor_agent":agent1,"seo_agent":agent2})
        agent3=_clean_json(agent3,{})
        if not agent3.get("executive_summary") or not agent3.get("critical_findings") and not agent3.get("opportunities"):
            agent3=_agent3_fallback(pack,agent1,agent2)
    except OllamaAgentError:
        raise
    if progress_callback: progress_callback(92,"Agent 3 completed · Finalizing intelligence report")
    return {"success":True,"provider":"Ollama","model":OLLAMA_MODEL,"target":target,"site_title":pack.get("site_title",""),"evidence":pack,
            "agents":{"competitor":agent1,"seo":agent2,"reviewer":agent3},"report":agent3}
