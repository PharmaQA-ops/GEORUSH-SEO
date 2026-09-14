from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from crawler import crawl
from score import calculate_score
from gsc import demo_data, fetch_search_analytics
from keywords import normalize_gsc_rows, summarize
from competitor import inspect_competitor, compare_domains

app=FastAPI(title="GEORUSH SEO API",version="0.7.0")
app.add_middleware(CORSMiddleware,allow_origins=["*"],allow_credentials=True,allow_methods=["*"],allow_headers=["*"])

class CrawlRequest(BaseModel):
    url:str
    max_pages:int=Field(default=25,ge=1,le=500)

@app.get("/api/health")
def health(): return {"status":"ok","service":"georush-seo-api","version":"0.7.0"}

@app.post("/api/crawl")
def start_crawl(req:CrawlRequest): result=crawl(req.url,req.max_pages)
    result["seo_score"]=calculate_score(result["results"])
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
    rows=normalize_gsc_rows({"rows":req.rows})
    return {"summary":summarize(rows),"rows":rows}


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
