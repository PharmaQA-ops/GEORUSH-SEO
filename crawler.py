import re, time, urllib.parse, urllib.robotparser
from collections import deque, Counter, defaultdict
from typing import Dict, List, Set
import httpx
from bs4 import BeautifulSoup

def normalize_url(url):
    p = urllib.parse.urlsplit(url)
    return urllib.parse.urlunsplit((p.scheme or "https", p.netloc.lower(), p.path or "/", p.query, ""))

def internal(url, host):
    try: return urllib.parse.urlsplit(url).netloc.lower() == host
    except: return False

def severity(issue):
    return {
        "HTTP_ERROR":"Critical","CRAWL_ERROR":"Critical","BROKEN_INTERNAL_LINK":"Critical",
        "NOINDEX":"High","CANONICAL_MISMATCH":"High","MISSING_CANONICAL":"High",
        "REDIRECT_CHAIN":"High","REDIRECT":"Medium","MISSING_TITLE":"High",
        "TITLE_TOO_LONG":"Medium","DUPLICATE_TITLE":"Medium",
        "MISSING_DESCRIPTION":"Medium","DESCRIPTION_TOO_LONG":"Low",
        "DUPLICATE_DESCRIPTION":"Medium","MISSING_H1":"Medium","MULTIPLE_H1":"Low",
        "THIN_CONTENT":"Medium","MISSING_IMAGE_ALT":"Low","ORPHAN_PAGE":"High",
        "DEEP_PAGE":"Medium","MIXED_CONTENT":"Medium"
    }.get(issue,"Info")

def parse(url, html, root_host):
    soup=BeautifulSoup(html,"lxml")
    title=soup.title.get_text(" ",strip=True) if soup.title else ""
    d=soup.find("meta",attrs={"name":re.compile("^description$",re.I)})
    desc=d.get("content","").strip() if d else ""
    h1=soup.find_all("h1")
    can=soup.find("link",rel=lambda v:v and "canonical" in v)
    canonical=urllib.parse.urljoin(url,can.get("href","").strip()) if can else ""
    r=soup.find("meta",attrs={"name":re.compile("^robots$",re.I)})
    robots=r.get("content","").lower() if r else ""
    text=soup.get_text(" ",strip=True)
    words=len(text.split())
    imgs=soup.find_all("img")
    missing_alt=sum(1 for x in imgs if not x.get("alt"))
    links=[]
    internal_links=[]
    external_links=[]
    for a in soup.find_all("a",href=True):
        u=urllib.parse.urljoin(url,a["href"])
        if u.startswith(("http://","https://")):
            links.append(normalize_url(u))
            (internal_links if internal(u,root_host) else external_links).append(normalize_url(u))
    issues=[]
    if not title: issues.append("MISSING_TITLE")
    elif len(title)>60: issues.append("TITLE_TOO_LONG")
    if not desc: issues.append("MISSING_DESCRIPTION")
    elif len(desc)>160: issues.append("DESCRIPTION_TOO_LONG")
    if not h1: issues.append("MISSING_H1")
    if len(h1)>1: issues.append("MULTIPLE_H1")
    if not canonical: issues.append("MISSING_CANONICAL")
    elif normalize_url(canonical)!=normalize_url(url): issues.append("CANONICAL_MISMATCH")
    if "noindex" in robots: issues.append("NOINDEX")
    if words<300: issues.append("THIN_CONTENT")
    if missing_alt: issues.append("MISSING_IMAGE_ALT")
    if url.startswith("https://"):
        for rtag in soup.find_all(src=True):
            if str(rtag.get("src","")).startswith("http://"): issues.append("MIXED_CONTENT"); break
    return dict(url=url,title=title,description=desc,h1_count=len(h1),h1=h1[0].get_text(" ",strip=True) if h1 else "",
                canonical=canonical,robots=robots,word_count=words,image_count=len(imgs),
                missing_alt=missing_alt,internal_links=len(internal_links),external_links=len(external_links),
                links=links,issues=issues)

def crawl(root_url,max_pages=25):
    root_url=normalize_url(root_url); host=urllib.parse.urlsplit(root_url).netloc.lower()
    rp=urllib.robotparser.RobotFileParser()
    robots_url=urllib.parse.urljoin(root_url,"/robots.txt")
    robots_available=False
    try: rp.set_url(robots_url); rp.read(); robots_available=True
    except: pass
    q=deque([root_url]); seen=set(); results=[]
    incoming=Counter()
    with httpx.Client(follow_redirects=True,timeout=15,headers={"User-Agent":"GEORUSH-SEO-Crawler/0.3"}) as c:
        while q and len(results)<max_pages:
            url=normalize_url(q.popleft())
            if url in seen or not internal(url,host): continue
            seen.add(url)
            if robots_available and not rp.can_fetch("GEORUSH-SEO-Crawler",url): continue
            t=time.perf_counter()
            try:
                resp=c.get(url); ms=round((time.perf_counter()-t)*1000)
                final=normalize_url(str(resp.url))
                if resp.is_success and "text/html" in resp.headers.get("content-type","").lower():
                    item=parse(final,resp.text,host)
                    item.update(status_code=resp.status_code,response_time_ms=ms,redirect=final!=url)
                    if final!=url: item["issues"].append("REDIRECT")
                    for link in item["links"]:
                        if internal(link,host):
                            incoming[link]+=1
                            if link not in seen and len(seen)+len(q)<max_pages*4: q.append(link)
                    item["links"]=None
                else:
                    item=dict(url=url,title="",description="",h1="",h1_count=0,canonical="",robots="",
                              word_count=0,image_count=0,missing_alt=0,internal_links=0,external_links=0,
                              status_code=resp.status_code,response_time_ms=ms,redirect=final!=url,
                              links=None,issues=["HTTP_ERROR"])
                results.append(item)
            except Exception as e:
                results.append(dict(url=url,title="",description="",h1="",h1_count=0,canonical="",robots="",
                    word_count=0,image_count=0,missing_alt=0,internal_links=0,external_links=0,
                    status_code=0,response_time_ms=0,redirect=False,links=None,
                    issues=["CRAWL_ERROR"],error=str(e)))
    # Duplicate detection
    for field, issue in [("title","DUPLICATE_TITLE"),("description","DUPLICATE_DESCRIPTION")]:
        groups=defaultdict(list)
        for x in results:
            val=(x.get(field) or "").strip().lower()
            if val: groups[val].append(x)
        for urls in groups.values():
            if len(urls)>1:
                for x in urls: x["issues"].append(issue)
    crawled={x["url"] for x in results}
    for x in results:
        if x["url"]!=root_url and incoming[x["url"]]==0: x["issues"].append("ORPHAN_PAGE")
        depth=max(0,len(urllib.parse.urlsplit(x["url"]).path.strip("/").split("/")) if urllib.parse.urlsplit(x["url"]).path.strip("/") else 0)
        x["page_depth"]=depth
        if depth>=4: x["issues"].append("DEEP_PAGE")
        x["severity_counts"]=dict(Counter(severity(i) for i in x["issues"]))
        x["issue_count"]=len(x["issues"])
    total=sum(x["issue_count"] for x in results)
    critical=sum(1 for x in results for i in x["issues"] if severity(i)=="Critical")
    high=sum(1 for x in results for i in x["issues"] if severity(i)=="High")
    health=max(0,round(100-(critical*12+high*7+max(0,total-critical-high)*3)))
    return {"root_url":root_url,"robots_available":robots_available,"sitemap_count":0,
            "pages":len(results),"health":health,"issues":total,
            "severity":{"Critical":critical,"High":high,
                        "Medium":sum(1 for x in results for i in x["issues"] if severity(i)=="Medium"),
                        "Low":sum(1 for x in results for i in x["issues"] if severity(i)=="Low")},
            "results":results}
