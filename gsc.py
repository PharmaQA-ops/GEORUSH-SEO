import os
from datetime import date, timedelta
import httpx

GSC_SCOPE = "https://www.googleapis.com/auth/webmasters.readonly"

def build_query(site_url, start_date=None, end_date=None, row_limit=25):
    end_date = end_date or date.today().isoformat()
    start_date = start_date or (date.today()-timedelta(days=28)).isoformat()
    return {
        "startDate": start_date, "endDate": end_date,
        "dimensions": ["query","page"],
        "rowLimit": row_limit
    }

async def fetch_search_analytics(access_token, site_url, start_date=None, end_date=None, row_limit=25):
    payload=build_query(site_url,start_date,end_date,row_limit)
    headers={"Authorization":f"Bearer {access_token}","Content-Type":"application/json"}
    encoded=site_url.replace("https://","https%3A%2F%2F").replace("/","%2F")
    url=f"https://searchconsole.googleapis.com/webmasters/v3/sites/{encoded}/searchAnalytics/query"
    async with httpx.AsyncClient(timeout=30) as client:
        r=await client.post(url,headers=headers,json=payload)
        r.raise_for_status()
        return r.json()

def demo_data():
    return {
        "connected": False,
        "message": "Configure Google OAuth credentials to connect Search Console.",
        "metrics": {"clicks":0,"impressions":0,"ctr":0,"position":0},
        "rows":[]
    }
