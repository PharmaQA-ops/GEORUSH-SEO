from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from crawler import crawl

app=FastAPI(title="GEORUSH SEO API",version="0.3.0")
app.add_middleware(CORSMiddleware,allow_origins=["*"],allow_credentials=True,allow_methods=["*"],allow_headers=["*"])

class CrawlRequest(BaseModel):
    url:str
    max_pages:int=Field(default=25,ge=1,le=500)

@app.get("/api/health")
def health(): return {"status":"ok","service":"georush-seo-api","version":"0.3.0"}

@app.post("/api/crawl")
def start_crawl(req:CrawlRequest): return crawl(req.url,req.max_pages)
