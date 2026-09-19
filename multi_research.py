"""GEORUSH Multi-Agent Deep Research.
Three AI research roles use the same evidence pack:
1) Competitor Researcher
2) SEO/Keyword Researcher
3) Critical Reviewer + Report Synthesizer
The web evidence is collected by GEORUSH itself; the AI agents do not get browser credentials.
"""
import json, os, re, time
from urllib.parse import urlparse
import httpx
from bs4 import BeautifulSoup

try:
    from google import genai
except Exception:
    genai = None

MODEL = os.getenv("GEMINI_RESEARCH_MODEL", os.getenv("GEMINI_MODEL", "gemini-3.8-flash"))


def _client():
    key = os.getenv("GEMINI_API_KEY", "").strip()
    if not key or genai is None:
        raise RuntimeError("GEMINI_API_KEY is not configured or google-genai is not installed")
    return genai.Client(api_key=key)


def _search(query, limit=8):
    try:
        r=httpx.get("https://html.duckduckgo.com/html/", params={"q":query}, headers={"User-Agent":"GEORUSH-Research/1.0"}, timeout=15, follow_redirects=True)
        r.raise_for_status(); soup=BeautifulSoup(r.text,"html.parser")
        out=[]
        for x in soup.select(".result")[:limit]:
            a=x.select_one(".result__a"); sn=x.select_one(".result__snippet")
            if a:
                out.append({"title":a.get_text(" ",strip=True),"url":a.get("href",""),"snippet":sn.get_text(" ",strip=True) if sn else ""})
        return out
    except Exception as e:
        return [{"error":str(e),"query":query}]


def _fetch(url, max_chars=18000):
    try:
        if not re.match(r"^https?://",url): url="https://"+url
        r=httpx.get(url,headers={"User-Agent":"GEORUSH-Research/1.0"},timeout=20,follow_redirects=True)
        soup=BeautifulSoup(r.text,"html.parser")
        for t in soup(["script","style","noscript","svg"]): t.decompose()
        text=" ".join(soup.stripped_strings)
        return {"url":url,"final_url":str(r.url),"status":r.status_code,"title":soup.title.get_text(" ",strip=True) if soup.title else "","text":text[:max_chars]}
    except Exception as e:
        return {"url":url,"error":str(e)}


def build_research_pack(target, keywords=None, competitor_limit=5):
    from competitor import discover_competitors, analyze_competitor_set
    keywords=[str(x).strip() for x in (keywords or []) if str(x).strip()]
    queries=[]
    if keywords: queries.extend(keywords[:5])
    else: queries.append(urlparse(target if '://' in target else 'https://'+target).netloc)
    search_results=[]
    for q in queries:
        search_results.extend(_search(q+" competitors",6))
    discovery=discover_competitors(target, keywords, competitor_limit)
    comps=[x.get("url") for x in discovery.get("competitors",[]) if x.get("url")]
    analysis=analyze_competitor_set(target,comps)
    urls=[target]+comps[:competitor_limit]
    pages=[_fetch(u,12000) for u in urls]
    return {"target":target,"keywords":keywords,"search_results":search_results[:30],"competitors":analysis,"pages":pages,"generated_at":time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime())}


def _call(client, system, evidence, previous=None):
    prompt = system + "\n\nEVIDENCE PACK:\n" + json.dumps(evidence,ensure_ascii=False,default=str)[:60000]
    if previous:
        prompt += "\n\nPRIOR AGENT OUTPUTS:\n" + json.dumps(previous,ensure_ascii=False,default=str)[:40000]
    res=client.models.generate_content(model=MODEL, contents=prompt)
    text=getattr(res,"text",None) or str(res)
    # tolerate markdown JSON fences
    m=re.search(r"\{.*\}",text,re.S)
    if m:
        try:return json.loads(m.group(0))
        except Exception: pass
    return {"raw":text}


def run_multi_research(target, keywords=None, competitor_limit=5):
    client=_client()
    pack=build_research_pack(target,keywords,competitor_limit)
    agent1=_call(client,"""You are GEORUSH Agent 1, the COMPETITOR RESEARCHER. Analyze the supplied public evidence. Identify the most relevant competitors, their observable services/content/technical signals, and concrete target-vs-competitor gaps. Never invent traffic, rankings, revenue or backlinks. Return JSON with: summary, competitors[{domain,why_relevant,observed_signals,gaps}], opportunities[], sources[].""",pack)
    agent2=_call(client,"""You are GEORUSH Agent 2, the SEO & KEYWORD RESEARCHER. Analyze the supplied public search results and pages. Infer search-intent/topic opportunities only when supported by evidence. Identify content gaps, keyword themes, SERP opportunities, technical/on-page opportunities and questions/topics. Clearly mark inference. Return JSON with: summary, keyword_themes[], content_gaps[], seo_opportunities[], cautions[], sources[].""",pack)
    agent3=_call(client,"""You are GEORUSH Agent 3, the CRITICAL REVIEWER and REPORT SYNTHESIZER. Cross-check Agent 1 and Agent 2 against the evidence. Reject unsupported claims, resolve contradictions conservatively, rank actions by evidence and business relevance without pretending to know Google rankings. Return JSON with: executive_summary, confidence, top_competitor, critical_findings[], opportunities[], action_plan[{timeframe,actions}], limitations[], sources[].""",pack,{"competitor_agent":agent1,"seo_agent":agent2})
    return {"success":True,"provider":"Google Gemini","model":MODEL,"target":target,"evidence":pack,"agents":{"competitor":agent1,"seo":agent2,"reviewer":agent3},"report":agent3}
