import os
import threading
import time
import uuid
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from crawler import crawl
from score import calculate_score
from gsc import demo_data, fetch_search_analytics
from keywords import normalize_gsc_rows, summarize
from keyword_intelligence import build_keyword_intelligence
from competitor import inspect_competitor, compare_domains, discover_competitors, analyze_competitor_set
from content import analyze_text
from analytics import analytics_summary
from radar import scan_url, get_result, radar_summary
from ai import ask, generate_report_recommendations, build_ai_context
from ollama_agent import run_agent as ollama_run_agent, OllamaAgentError
from multi_research import run_multi_research

app = FastAPI(title="GEORUSH SEO API", version="0.32.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

SEARCH_INDEX = []
LAST_CRAWL = {}

class CrawlRequest(BaseModel):
    url: str
    max_pages: int = Field(default=25, ge=1, le=500)

@app.get("/api/health")
def health():
    return {"status": "ok", "service": "georush-seo-api", "version": "0.32.0"}

@app.post("/api/crawl")
def start_crawl(req: CrawlRequest):
    global SEARCH_INDEX, LAST_CRAWL
    result = crawl(req.url, req.max_pages)
    result["seo_score"] = calculate_score(result.get("results", []))
    SEARCH_INDEX = result.get("results", [])
    LAST_CRAWL = result
    return result

class GSCRequest(BaseModel):
    access_token: str
    site_url: str
    start_date: str | None = None
    end_date: str | None = None
    row_limit: int = Field(default=25, ge=1, le=25000)

@app.get("/api/gsc/demo")
def gsc_demo():
    return demo_data()

@app.post("/api/gsc/search-analytics")
async def gsc_search(req: GSCRequest):
    return await fetch_search_analytics(
        req.access_token, req.site_url, req.start_date, req.end_date, req.row_limit
    )

class KeywordRowsRequest(BaseModel):
    rows: list = Field(default_factory=list)

@app.post("/api/keywords/analyze")
def analyze_keywords(req: KeywordRowsRequest):
    rows = normalize_gsc_rows({"rows": req.rows})
    return {"summary": summarize(rows), "rows": rows}

class KeywordIntelligenceRequest(BaseModel):
    target: str
    seed_keywords: list[str] = Field(default_factory=list)
    limit: int = Field(default=40, ge=5, le=100)

@app.post("/api/keywords/intelligence")
def keyword_intelligence(req: KeywordIntelligenceRequest):
    crawl = LAST_CRAWL.get("results", []) if LAST_CRAWL else SEARCH_INDEX
    return build_keyword_intelligence(req.target, crawl, req.seed_keywords, req.limit)

@app.get("/api/site/profile")
def site_profile(url: str):
    profile = inspect_competitor(url)
    signals = profile.get("signals", {})
    return {"url": url, "title": signals.get("title", ""), "description": signals.get("description", ""),
            "h1": signals.get("h1", []), "h2": signals.get("h2", []), "status": profile.get("status", 0),
            "domain": profile.get("domain", ""), "signals": signals}

class CompetitorRequest(BaseModel):
    url: str

class CompetitorCompareRequest(BaseModel):
    target: str
    competitors: list[str] = Field(default_factory=list)

@app.post("/api/competitor/inspect")
def competitor_inspect(req: CompetitorRequest):
    return inspect_competitor(req.url)

@app.post("/api/competitor/compare")
def competitor_compare(req: CompetitorCompareRequest):
    return compare_domains(req.target, req.competitors[:10])


def _crawl_topic_seeds(target):
    seeds=[]
    try:
        host=target.lower().replace("https://","").replace("http://","").split("/")[0]
        for item in (LAST_CRAWL.get("results",[]) if LAST_CRAWL else SEARCH_INDEX):
            if host in str(item.get("url","")).lower():
                for value in [item.get("title",""),item.get("h1","")]:
                    if value and value not in seeds: seeds.append(value)
                if seeds: break
    except Exception: pass
    return seeds

class AutoCompetitorRequest(BaseModel):
    target: str
    keywords: list[str] = Field(default_factory=list)
    limit: int = Field(default=5, ge=1, le=10)

@app.post("/api/competitor/discover")
def competitor_discover(req: AutoCompetitorRequest):
    seeds=list(req.keywords or [])
    if not seeds: seeds=_crawl_topic_seeds(req.target)
    found=discover_competitors(req.target, seeds, req.limit)
    urls=[x["url"] for x in found.get("competitors",[])]
    analysis=analyze_competitor_set(req.target, urls)
    if not found.get("site_title"):
        profile=_crawl_topic_seeds(req.target)
        found["site_title"]=profile[0] if profile else analysis.get("target",{}).get("signals",{}).get("title","")
    return {**found, **analysis}

class RadarRequest(BaseModel):
    url: str

@app.post("/api/radar/scan")
def radar_scan(req: RadarRequest):
    submission=scan_url(req.url)
    if submission.get("scan",{}).get("uuid"):
        submission["result"]=get_result(submission["scan"]["uuid"])
        submission["summary"]=radar_summary(req.url, submission["result"])
    else:
        submission["summary"]=radar_summary(req.url)
    return submission

class IntelligenceRequest(BaseModel):
    target: str
    keywords: list[str] = Field(default_factory=list)
    competitor_limit: int = Field(default=5, ge=1, le=10)
    radar: bool = True

@app.post("/api/intelligence/full")
def full_intelligence(req: IntelligenceRequest):
    target=req.target
    discovery=discover_competitors(target, req.keywords, req.competitor_limit)
    urls=[x["url"] for x in discovery.get("competitors",[])]
    comp=analyze_competitor_set(target, urls)
    radar_data={}
    if req.radar:
        submission=scan_url(target)
        radar_data=submission
        if submission.get("scan",{}).get("uuid"):
            radar_data["result"]=get_result(submission["scan"]["uuid"])
            radar_data["summary"]=radar_summary(target, radar_data["result"])
        else:
            radar_data["summary"]=radar_summary(target)
    crawl = LAST_CRAWL or {"results":SEARCH_INDEX,"pages":len(SEARCH_INDEX),"issues":sum(len(x.get("issues",[]) or []) for x in SEARCH_INDEX)}
    # Score isn't retained separately in the API index, so the report can still use issue-level context.
    context=build_ai_context(crawl=crawl, keywords=req.keywords, competitors=comp.get("competitors",[]), radar=radar_data.get("summary",{}))
    ai=generate_report_recommendations(crawl=crawl, competitors=comp.get("competitors",[]), keywords=req.keywords, radar=radar_data.get("summary",{}))
    agent_context={
        "target": target,
        "crawl": crawl,
        "keywords":[{"query": str(k)} for k in req.keywords],
        "competitors": comp.get("competitors",[]),
        "competitor_analysis": comp,
        "radar": radar_data.get("summary",{}),
    }
    try:
        ollama = ollama_run_agent("""You are the GEORUSH AI SEO Analyst. Analyze the supplied crawl, competitor, keyword and Radar evidence. Produce JSON with overall_priority, executive_summary, recommendations[{priority,area,finding,recommendation,evidence,affected_urls}], action_plan[{timeframe,actions}], data_gaps[]. Do not invent rankings, traffic, backlinks, revenue or penalties.""", agent_context)
        ollama = {"success": True, "provider": "Ollama", **ollama}
    except OllamaAgentError as exc:
        ollama={"success":False,"error":str(exc),"mode":"configuration_or_runtime_error","provider":"Ollama"}
    except Exception as exc:
        ollama={"success":False,"error":f"Ollama agent failed: {exc}","mode":"runtime_error","provider":"Ollama"}
    return {"target":target,"competitors":comp,"radar":radar_data,"recommendations":ai,"ai":context,"ollama":ollama}


class DeepResearchRequest(BaseModel):
    target: str
    keywords: list[str] = Field(default_factory=list)
    competitor_limit: int = Field(default=5, ge=1, le=10)

# Long-running research jobs run in a background thread so the browser does not
# have to keep one HTTP request open for the entire multi-agent run.
RESEARCH_JOBS = {}
RESEARCH_LOCK = threading.Lock()

def _run_research_job(job_id: str, req: DeepResearchRequest):
    def progress(value, stage):
        with RESEARCH_LOCK:
            if job_id in RESEARCH_JOBS:
                RESEARCH_JOBS[job_id].update({"progress": int(value), "stage": stage})
    with RESEARCH_LOCK:
        RESEARCH_JOBS[job_id] = {"job_id": job_id, "status": "running", "progress": 5, "stage": "Preparing web research", "started_at": time.time()}
    try:
        progress(12, "Collecting target title and topic signals")
        seeds=list(req.keywords or []) or _crawl_topic_seeds(req.target)
        result = run_multi_research(req.target, seeds, req.competitor_limit, progress_callback=progress)
        with RESEARCH_LOCK:
            RESEARCH_JOBS[job_id].update({"status": "completed", "progress": 100, "stage": "Research completed · Report ready", "result": result, "finished_at": time.time()})
    except Exception as exc:
        with RESEARCH_LOCK:
            RESEARCH_JOBS[job_id].update({"status": "failed", "progress": 100, "stage": "Research failed", "error": str(exc), "finished_at": time.time()})

@app.post("/api/research/multi-agent/start")
def start_multi_agent_research(req: DeepResearchRequest):
    job_id = uuid.uuid4().hex
    with RESEARCH_LOCK:
        RESEARCH_JOBS[job_id] = {"job_id": job_id, "status": "queued", "progress": 0, "stage": "Queued", "target": req.target, "started_at": None}
    threading.Thread(target=_run_research_job, args=(job_id, req), daemon=True).start()
    return {"success": True, "job_id": job_id, "status": "queued", "provider": "Ollama Multi-Agent Research"}

@app.get("/api/research/multi-agent/status/{job_id}")
def multi_agent_research_status(job_id: str):
    with RESEARCH_LOCK:
        job = RESEARCH_JOBS.get(job_id)
        if not job:
            return {"success": False, "error": "RESEARCH_JOB_NOT_FOUND"}
        return {"success": True, **job}

# Backward-compatible synchronous endpoint for other API clients.
@app.post("/api/research/multi-agent")
def multi_agent_research(req: DeepResearchRequest):
    try:
        return run_multi_research(req.target, req.keywords, req.competitor_limit)
    except Exception as exc:
        return {"success":False,"error":str(exc),"provider":"Ollama Multi-Agent Research"}

class GeminiAgentRequest(BaseModel):
    target: str
    keywords: list[dict] = Field(default_factory=list)
    use_existing_intelligence: bool = True

@app.get("/api/ai/status")
def ai_status():
    from ollama_agent import status as ollama_status
    return ollama_status()

@app.get("/api/ai/ollama/status")
def ollama_status_endpoint():
    from ollama_agent import status as ollama_status
    return ollama_status()

class OllamaAgentRequest(BaseModel):
    target: str
    keywords: list[dict] = Field(default_factory=list)
    use_existing_intelligence: bool = True

@app.post("/api/ai/ollama")
def ollama_ai(req: OllamaAgentRequest):
    crawl = LAST_CRAWL or {"results": SEARCH_INDEX, "pages": len(SEARCH_INDEX), "issues": sum(len(x.get("issues", []) or []) for x in SEARCH_INDEX)}
    competitor_data = {}
    radar_data = {}
    if req.use_existing_intelligence:
        try:
            discovery = discover_competitors(req.target, [str(k.get("query", "")) for k in req.keywords if isinstance(k, dict)], 5)
            urls = [x["url"] for x in discovery.get("competitors", [])]
            competitor_data = analyze_competitor_set(req.target, urls)
        except Exception as exc:
            competitor_data = {"error": str(exc), "competitors": []}
        try:
            submission = scan_url(req.target)
            radar_data = submission
            if submission.get("scan", {}).get("uuid"):
                radar_data["result"] = get_result(submission["scan"]["uuid"])
                radar_data["summary"] = radar_summary(req.target, radar_data["result"])
            else:
                radar_data["summary"] = radar_summary(req.target)
        except Exception as exc:
            radar_data = {"error": str(exc), "summary": {"configured": False}}
    context = {
        "target": req.target,
        "crawl": crawl,
        "keywords": req.keywords,
        "competitors": competitor_data.get("competitors", []),
        "competitor_analysis": competitor_data,
        "radar": radar_data.get("summary", radar_data),
    }
    try:
        result = ollama_run_agent("""You are the GEORUSH AI SEO Analyst. Analyze the supplied evidence and return JSON with overall_priority, executive_summary, recommendations[{priority,area,finding,recommendation,evidence,affected_urls}], action_plan[{timeframe,actions}], data_gaps[]. Do not invent facts.""", context)
        return {"success": True, "provider": "Ollama", "model": os.getenv("OLLAMA_MODEL", "qwen3:0.6b"), **result}
    except OllamaAgentError as exc:
        return {"success": False, "error": str(exc), "provider": "Ollama", "mode": "runtime_error"}
    except Exception as exc:
        return {"success": False, "error": f"Ollama agent failed: {exc}", "provider": "Ollama", "mode": "runtime_error"}

class SearchRequest(BaseModel):
    query: str
    limit: int = Field(default=25, ge=1, le=500)

@app.post("/api/search")
def search(req: SearchRequest):
    q = req.query.strip().lower()
    if not q:
        return {"query": req.query, "results": []}

    matches = []
    for item in SEARCH_INDEX:
        hay = " ".join([
            str(item.get("url", "")),
            str(item.get("title", "")),
            str(item.get("description", "")),
            str(item.get("h1", "")),
            " ".join(item.get("issues", []) or []),
        ]).lower()
        if q in hay:
            matches.append(item)

    return {"query": req.query, "results": matches[:req.limit]}

class ContentRequest(BaseModel):
    text: str
    keyword: str = ""

@app.post("/api/content/analyze")
def content_analyze(req: ContentRequest):
    return analyze_text(req.text, req.keyword)

@app.get("/api/analytics/summary")
def analytics():
    return analytics_summary()

class AIRequest(BaseModel):
    question: str
    context: dict = Field(default_factory=dict)

@app.post("/api/ai/ask")
def ai_ask(req: AIRequest):
    return ask(req.question, req.context)

# Desktop/web frontend assets. This MUST be mounted after /api routes so
# FastAPI routes remain available while the UI loads CSS/JS from the same origin.
FRONTEND_DIR = os.path.dirname(os.path.abspath(__file__))
app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")
