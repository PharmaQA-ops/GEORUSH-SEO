from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from crawler import crawl
from score import calculate_score
from gsc import demo_data, fetch_search_analytics

app=FastAPI(title="GEORUSH SEO API",version="0.5.0")
app.add_middleware(CORSMiddleware,allow_origins=["*"],allow_credentials=True,allow_methods=["*"],allow_headers=["*"])

class CrawlRequest(BaseModel):
    url:str
    max_pages:int=Field(default=25,ge=1,le=500)

@app.get("/api/health")
def health(): return {"status":"ok","service":"georush-seo-api","version":"0.5.0"}

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
