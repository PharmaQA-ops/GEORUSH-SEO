
import re, time, urllib.parse
from collections import Counter
import httpx
from bs4 import BeautifulSoup

def normalize(url):
    if not url: return ""
    if not re.match(r"^https?://", url, re.I): url="https://"+url
    p=urllib.parse.urlsplit(url)
    return urllib.parse.urlunsplit((p.scheme or "https",p.netloc.lower(),p.path or "/",p.query,""))

def root_domain(url):
    host=urllib.parse.urlsplit(normalize(url)).netloc.lower().split(":")[0]
    parts=host.split(".")
    return ".".join(parts[-2:]) if len(parts)>=2 else host

def extract_signals(url, html):
    soup=BeautifulSoup(html,"lxml")
    title=soup.title.get_text(" ",strip=True) if soup.title else ""
    desc=soup.find("meta",attrs={"name":re.compile("^description$",re.I)})
    desc=desc.get("content","").strip() if desc else ""
    h1=[x.get_text(" ",strip=True) for x in soup.find_all("h1")]
    h2=[x.get_text(" ",strip=True) for x in soup.find_all("h2")]
    text=soup.get_text(" ",strip=True)
    words=len(text.split())
    links=[]
    for a in soup.find_all("a",href=True):
        u=urllib.parse.urljoin(url,a["href"])
        if u.startswith(("http://","https://")): links.append(normalize(u))
    return {
        "url":url,"title":title,"description":desc,"h1_count":len(h1),
        "h1":h1[:10],"h2_count":len(h2),"word_count":words,
        "internal_links":len(set(x for x in links if urllib.parse.urlsplit(x).netloc==urllib.parse.urlsplit(url).netloc)),
        "external_links":len(set(x for x in links if urllib.parse.urlsplit(x).netloc!=urllib.parse.urlsplit(url).netloc)),
        "https": urllib.parse.urlsplit(url).scheme=="https",
        "canonical": bool(soup.find("link",rel=lambda x: x and "canonical" in x)),
        "image_count":len(soup.find_all("img")),
        "images_missing_alt":sum(1 for x in soup.find_all("img") if not x.get("alt")),
    }

def inspect_competitor(url):
    url=normalize(url)
    start=time.perf_counter()
    try:
        with httpx.Client(follow_redirects=True,timeout=15,headers={"User-Agent":"GEORUSH-SEO-Competitor/1.0"}) as c:
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

def _search_ddg(query, limit=10):
    """Best-effort public web discovery. For higher-volume use, set SERPER_API_KEY."""
    headers={"User-Agent":"Mozilla/5.0 (compatible; GEORUSH-SEO/1.0)"}
    url="https://html.duckduckgo.com/html/"
    with httpx.Client(timeout=15,headers=headers,follow_redirects=True) as c:
        r=c.get(url,params={"q":query})
        r.raise_for_status()
    soup=BeautifulSoup(r.text,"lxml")
    out=[]
    for a in soup.select("a.result__a"):
        href=a.get("href","")
        if href.startswith("http"):
            out.append({"url":href,"title":a.get_text(" ",strip=True)})
        if len(out)>=limit: break
    return out

def discover_competitors(target, keywords=None, limit=5):
    target=normalize(target); td=root_domain(target)
    keywords=keywords or []
    # Prefer explicit keyword signals, then target hostname.
    query=" ".join(str(x).strip() for x in keywords[:4] if str(x).strip())
    if not query:
        query=td
    candidates=[]
    try:
        candidates=_search_ddg(query, max(10,limit*4))
    except Exception as e:
        return {"target":target,"query":query,"competitors":[],"error":str(e)}
    seen={td,"www."+td}
    comps=[]
    for item in candidates:
        u=normalize(item["url"]); d=root_domain(u)
        if not d or d in seen or "duckduckgo" in d: continue
        # Skip obvious directories/social/search engines.
        if any(x in d for x in ["facebook.com","instagram.com","linkedin.com","youtube.com","wikipedia.org","google.com"]): continue
        seen.add(d)
        comps.append({"url":u,"title":item.get("title","")})
        if len(comps)>=limit: break
    return {"target":target,"query":query,"competitors":comps}

def score_signal(s):
    # Comparable homepage signal score; not a search ranking.
    score=0
    if s.get("https"): score+=15
    if s.get("title") and len(s["title"])<=60: score+=15
    if s.get("description") and len(s["description"])<=160: score+=15
    if s.get("h1_count")==1: score+=15
    if s.get("canonical"): score+=10
    if s.get("images_missing_alt",0)==0: score+=10
    if s.get("word_count",0)>=300: score+=10
    if s.get("internal_links",0)>=5: score+=10
    return score

def analyze_competitor_set(target, competitor_urls, target_result=None):
    target_result=target_result or inspect_competitor(target)
    target_s=target_result.get("signals",{})
    comps=[inspect_competitor(x) for x in competitor_urls[:10]]
    target_score=score_signal(target_s)
    for c in comps:
        c["signal_score"]=score_signal(c.get("signals",{}))
        c["gaps_vs_target"]={
            "word_count":c.get("signals",{}).get("word_count",0)-target_s.get("word_count",0),
            "h1_count":c.get("signals",{}).get("h1_count",0)-target_s.get("h1_count",0),
            "response_time_ms":c.get("response_time_ms",0)-target_result.get("response_time_ms",0)
        }
    ordered=sorted(comps,key=lambda x:x.get("signal_score",0),reverse=True)
    return {"target":target_result,"target_signal_score":target_score,
            "competitors":ordered,
            "top_competitor":ordered[0] if ordered else None}
