import re, time, urllib.parse
from collections import Counter
import httpx
from bs4 import BeautifulSoup

def normalize(url):
    p=urllib.parse.urlsplit(url)
    return urllib.parse.urlunsplit((p.scheme or "https",p.netloc.lower(),p.path or "/",p.query,""))

def extract_signals(url, html):
    soup=BeautifulSoup(html,"lxml")
    title=soup.title.get_text(" ",strip=True) if soup.title else ""
    desc=soup.find("meta",attrs={"name":re.compile("^description$",re.I)})
    desc=desc.get("content","").strip() if desc else ""
    h1=[x.get_text(" ",strip=True) for x in soup.find_all("h1")]
    text=soup.get_text(" ",strip=True)
    words=len(text.split())
    links=[]
    for a in soup.find_all("a",href=True):
        u=urllib.parse.urljoin(url,a["href"])
        if u.startswith(("http://","https://")): links.append(normalize(u))
    return {"url":url,"title":title,"description":desc,"h1_count":len(h1),
            "word_count":words,"internal_links":len(set(x for x in links if urllib.parse.urlsplit(x).netloc==urllib.parse.urlsplit(url).netloc)),
            "external_links":len(set(x for x in links if urllib.parse.urlsplit(x).netloc!=urllib.parse.urlsplit(url).netloc))}

def inspect_competitor(url):
    url=normalize(url)
    start=time.perf_counter()
    try:
        with httpx.Client(follow_redirects=True,timeout=15,headers={"User-Agent":"GEORUSH-SEO-Competitor/0.7"}) as c:
            r=c.get(url)
        ms=round((time.perf_counter()-start)*1000)
        if "text/html" not in r.headers.get("content-type","").lower():
            return {"url":url,"status":r.status_code,"response_time_ms":ms,"signals":{},"error":"Not HTML"}
        return {"url":url,"status":r.status_code,"response_time_ms":ms,
                "final_url":normalize(str(r.url)),"signals":extract_signals(str(r.url),r.text)}
    except Exception as e:
        return {"url":url,"status":0,"response_time_ms":0,"signals":{},"error":str(e)}

def compare_domains(target, competitors):
    return {"target":inspect_competitor(target),
            "competitors":[inspect_competitor(x) for x in competitors]}
