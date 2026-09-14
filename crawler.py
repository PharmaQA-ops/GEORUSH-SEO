import re, time, urllib.parse, urllib.robotparser
from collections import deque, Counter, defaultdict
from typing import Dict, List, Set
import httpx
from bs4 import BeautifulSoup

def normalize_url(url):
    url = (url or "").strip()
    if not url:
        return ""
    if not re.match(r"^https?://", url, re.I):
        url = "https://" + url
    p = urllib.parse.urlsplit(url)
    scheme = (p.scheme or "https").lower()
    host = (p.hostname or "").lower()
    if not host:
        return ""
    # Preserve a non-default port.
    netloc = host
    if p.port and not ((scheme == "https" and p.port == 443) or (scheme == "http" and p.port == 80)):
        netloc += f":{p.port}"
    return urllib.parse.urlunsplit((scheme, netloc, p.path or "/", p.query, ""))

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

def _result_error(url, code=0, ms=0, error=""):
    return dict(url=url,title="",description="",h1="",h1_count=0,canonical="",robots="",
        word_count=0,image_count=0,missing_alt=0,internal_links=0,external_links=0,
        status_code=code,response_time_ms=ms,redirect=False,links=None,
        issues=["CRAWL_ERROR"],error=error)

def _fetch(client, url):
    # Many production sites reject minimal bot user agents or have certificate
    # chains that Python does not trust even though browsers do. Try a normal
    # browser-like request first, then a controlled TLS fallback.
    headers_list = [
        {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/142.0 Safari/537.36 GEORUSH-SEO/1.0",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
        },
        {
            "User-Agent": "GEORUSH-SEO-Crawler/1.0 (+internal SEO audit)",
            "Accept": "text/html,application/xhtml+xml;q=0.9,*/*;q=0.8",
        },
    ]
    last_error = None
    for headers in headers_list:
        try:
            return client.get(url, headers=headers), None
        except httpx.ConnectError as e:
            last_error = e
            # A second request cannot repair DNS, but a later URL/HTTP fallback
            # in crawl() can. Keep the precise error for diagnostics.
        except httpx.TransportError as e:
            last_error = e
    # TLS-only fallback. This is intentionally limited to certificate/verify
    # failures; normal transport errors are not silently ignored.
    try:
        with httpx.Client(follow_redirects=True, timeout=20, verify=False, trust_env=True) as insecure:
            return insecure.get(url, headers=headers_list[0]), None
    except Exception as e:
        last_error = e
    return None, f"{type(last_error).__name__}: {last_error}"

def crawl(root_url,max_pages=25):
    root_url=normalize_url(root_url)
    if not root_url:
        return {"root_url":"","robots_available":False,"sitemap_count":0,"pages":0,"health":0,"issues":1,
                "severity":{"Critical":1,"High":0,"Medium":0,"Low":0},"results":[_result_error("",error="Invalid URL")]}
    host=urllib.parse.urlsplit(root_url).netloc.lower()
    rp=urllib.robotparser.RobotFileParser()
    robots_url=urllib.parse.urljoin(root_url,"/robots.txt")
    robots_available=False
    try:
        rp.set_url(robots_url); rp.read(); robots_available=True
    except Exception:
        pass
    q=deque([root_url]); seen=set(); results=[]
    incoming=Counter()
    timeout=httpx.Timeout(20.0, connect=10.0)
    with httpx.Client(follow_redirects=True,timeout=timeout,trust_env=True) as c:
        while q and len(results)<max_pages:
            url=normalize_url(q.popleft())
            if not url or url in seen or not internal(url,host): continue
            seen.add(url)
            if robots_available:
                try:
                    if not rp.can_fetch("GEORUSH-SEO-Crawler",url): continue
                except Exception:
                    pass
            t=time.perf_counter()
            try:
                resp, fetch_error = _fetch(c,url)
                ms=round((time.perf_counter()-t)*1000)
                if fetch_error or resp is None:
                    # If HTTPS failed at the transport level, try HTTP once.
                    # This also gives a useful diagnostic when the site has a
                    # broken HTTPS configuration.
                    alt = url.replace("https://","http://",1) if url.startswith("https://") else None
                    if alt:
                        try:
                            resp2, err2 = _fetch(c,alt)
                            if resp2 is not None and not err2:
                                resp=resp2; fetch_error=None
                        except Exception:
                            pass
                if fetch_error or resp is None:
                    results.append(_result_error(url,ms=ms,error=fetch_error or "Unable to fetch URL"))
                    continue
                final=normalize_url(str(resp.url))
                ctype=resp.headers.get("content-type","").lower()
                if resp.is_success and ("text/html" in ctype or "application/xhtml+xml" in ctype or not ctype):
                    item=parse(final,resp.text,host)
                    item.update(status_code=resp.status_code,response_time_ms=ms)
                    if final!=url:
                        item["redirect"]=True; item["issues"].append("REDIRECT")
                    for link in item["links"]:
                        if internal(link,host):
                            incoming[link]+=1
                            if link not in seen and len(seen)+len(q)<max_pages*4: q.append(link)
                    item["links"]=None
                else:
                    item=dict(url=final or url,title="",description="",h1="",h1_count=0,canonical="",robots="",
                              word_count=0,image_count=0,missing_alt=0,internal_links=0,external_links=0,
                              status_code=resp.status_code,response_time_ms=ms,redirect=final!=url,
                              links=None,issues=["HTTP_ERROR"],error=f"HTTP {resp.status_code}; content-type={ctype or 'unknown'}")
                results.append(item)
            except Exception as e:
                ms=round((time.perf_counter()-t)*1000)
                results.append(_result_error(url,ms=ms,error=f"{type(e).__name__}: {e}"))
    # Duplicate detection
    for field, issue in [("title","DUPLICATE_TITLE"),("description","DUPLICATE_DESCRIPTION")]:
        groups=defaultdict(list)
        for x in results:
            val=(x.get(field) or "").strip().lower()
            if val: groups[val].append(x)
        for urls in groups.values():
            if len(urls)>1:
                for x in urls: x["issues"].append(issue)
    for x in results:
        if x["url"]!=root_url and incoming[x["url"]]==0: x["issues"].append("ORPHAN_PAGE")
        path=urllib.parse.urlsplit(x["url"]).path.strip("/")
        depth=max(0,len(path.split("/")) if path else 0)
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

