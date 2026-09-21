import re, time, urllib.parse
from collections import Counter
import httpx
from bs4 import BeautifulSoup

GENERIC_SKIP = {
    "facebook.com","instagram.com","linkedin.com","youtube.com","wikipedia.org",
    "google.com","bing.com","duckduckgo.com","reddit.com","pinterest.com"
}
TOPIC_TERMS = {
    "logistics","freight","cargo","forwarding","transport","transportation",
    "defence","defense","aerospace","military","aviation","air","ocean",
    "dangerous goods","dg","project logistics","security","supply chain",
    "ammunition","uav","drone","uavs","cold chain","pharma"
}

def normalize(url):
    if not url: return ""
    if not re.match(r"^https?://", url, re.I): url="https://"+url
    p=urllib.parse.urlsplit(url)
    return urllib.parse.urlunsplit((p.scheme or "https",p.netloc.lower(),p.path or "/",p.query,""))

def root_domain(url):
    host=urllib.parse.urlsplit(normalize(url)).netloc.lower().split(":")[0]
    parts=host.split(".")
    return ".".join(parts[-2:]) if len(parts)>=2 else host

def _fetch_html(url):
    url=normalize(url)
    try:
        with httpx.Client(follow_redirects=True,timeout=20,headers={"User-Agent":"Mozilla/5.0 (compatible; GEORUSH-SEO/1.0)"}) as c:
            r=c.get(url)
        return r
    except Exception:
        return None

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
        "url":url,"title":title,"description":desc,"h1_count":len(h1),"h1":h1[:10],
        "h2_count":len(h2),"h2":h2[:12],"word_count":words,
        "internal_links":len(set(x for x in links if urllib.parse.urlsplit(x).netloc==urllib.parse.urlsplit(url).netloc)),
        "external_links":len(set(x for x in links if urllib.parse.urlsplit(x).netloc!=urllib.parse.urlsplit(url).netloc)),
        "https":urllib.parse.urlsplit(url).scheme=="https",
        "canonical":bool(soup.find("link",rel=lambda x:x and "canonical" in x)),
        "image_count":len(soup.find_all("img")),
        "images_missing_alt":sum(1 for x in soup.find_all("img") if not x.get("alt")),
    }

def inspect_competitor(url):
    url=normalize(url)
    start=time.perf_counter()
    r=_fetch_html(url)
    ms=round((time.perf_counter()-start)*1000)
    if r is None:
        return {"url":url,"domain":root_domain(url),"status":0,"response_time_ms":ms,"signals":{},"error":"Unable to fetch URL"}
    if "text/html" not in r.headers.get("content-type","").lower() and r.status_code>=300:
        return {"url":url,"domain":root_domain(url),"status":r.status_code,"response_time_ms":ms,"signals":{},"error":"Not HTML"}
    final=normalize(str(r.url))
    return {"url":url,"domain":root_domain(final or url),"status":r.status_code,"response_time_ms":ms,
            "final_url":final,"signals":extract_signals(final or url,r.text)}

def compare_domains(target, competitors):
    return {"target":inspect_competitor(target),"competitors":[inspect_competitor(x) for x in competitors]}

def _search_ddg(query, limit=10):
    headers={"User-Agent":"Mozilla/5.0 (compatible; GEORUSH-SEO/1.0)"}
    with httpx.Client(timeout=15,headers=headers,follow_redirects=True) as c:
        r=c.get("https://html.duckduckgo.com/html/",params={"q":query})
        r.raise_for_status()
    soup=BeautifulSoup(r.text,"lxml")
    out=[]
    for result in soup.select(".result"):
        a=result.select_one("a.result__a")
        sn=result.select_one(".result__snippet")
        if not a: continue
        out.append({"url":a.get("href",""),"title":a.get_text(" ",strip=True),
                    "snippet":sn.get_text(" ",strip=True) if sn else ""})
        if len(out)>=limit: break
    return out

def _topic_tokens(text):
    words=re.findall(r"[A-Za-z][A-Za-z0-9+&/-]{2,}",str(text).lower())
    stop={"the","and","for","with","from","into","that","this","your","our","company","home","about","more","india","services","service","contact","global","international","best","top","leading"}
    return [w for w in words if w not in stop]

def _candidate_score(item, topic_terms):
    text=(item.get("title","")+" "+item.get("snippet","")).lower()
    score=0
    for term in topic_terms:
        if term in text: score += 3 if " " in term else 2
    if any(t in text for t in ["logistics","freight","cargo","forwarding","transport"]): score+=3
    if any(t in text for t in ["directory","jobs","wikipedia","market report"]): score-=5
    return score

def discover_competitors(target, keywords=None, limit=5):
    target=normalize(target); td=root_domain(target); keywords=keywords or []
    target_info=inspect_competitor(target)
    sig=target_info.get("signals",{})
    title=sig.get("title","")
    h1=" ".join(sig.get("h1",[])[:4])
    h2=" ".join(sig.get("h2",[])[:5])
    seed_terms=[str(x).strip() for x in keywords[:6] if str(x).strip()]
    base_text=" ".join(seed_terms+[title,h1,h2])
    tokens=_topic_tokens(base_text)
    topic_terms=[]
    for phrase in ["defence logistics","defense logistics","aerospace logistics","military logistics","dangerous goods logistics","project logistics","pharmaceutical logistics","air freight","ocean freight","drone logistics"]:
        if any(t in phrase for t in tokens) or phrase in base_text.lower(): topic_terms.append(phrase)
    if not topic_terms:
        topic_terms=["logistics","freight forwarding","cargo"]
    queries=[]
    for q in [*seed_terms[:3],*topic_terms[:4]]:
        q=" ".join(q.split())
        if q and q not in queries: queries.append(q)
    if not queries: queries=[root_domain(target)]
    candidates=[]; errors=[]
    for q in queries[:6]:
        try: candidates.extend(_search_ddg(q,8))
        except Exception as e: errors.append(f"{q}: {e}")
    seen={td}; scored=[]
    for item in candidates:
        u=normalize(item.get("url","")); d=root_domain(u)
        if not d or d in seen or d in GENERIC_SKIP: continue
        if any(x in d for x in ["mordorintelligence.com","owler.com","crunchbase.com","clutch.co"]): continue
        s=_candidate_score(item,topic_terms)
        if s<3: continue
        seen.add(d); scored.append({**item,"domain":d,"relevance_score":s})
    scored.sort(key=lambda x:x["relevance_score"],reverse=True)
    comps=scored[:limit]
    return {"target":target,"site_title":title,"query_terms":topic_terms,"competitors":comps,
            "errors":errors,"target_profile":target_info}

def score_signal(s):
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
        cs=c.get("signals",{})
        c["gaps_vs_target"]={
            "word_count":cs.get("word_count",0)-target_s.get("word_count",0),
            "h1_count":cs.get("h1_count",0)-target_s.get("h1_count",0),
            "response_time_ms":c.get("response_time_ms",0)-target_result.get("response_time_ms",0),
            "title_present":bool(cs.get("title")),
            "description_present":bool(cs.get("description")),
            "canonical_present":bool(cs.get("canonical")),
        }
    ordered=sorted(comps,key=lambda x:(x.get("signal_score",0),x.get("signals",{}).get("word_count",0)),reverse=True)
    return {"target":target_result,"target_signal_score":target_score,"competitors":ordered,
            "top_competitor":ordered[0] if ordered else None}
