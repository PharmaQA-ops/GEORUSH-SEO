"""Evidence-based keyword intelligence without pretending to have search volume/rank data."""
import re
from collections import Counter, defaultdict
import httpx
from bs4 import BeautifulSoup
from keywords import classify_intent

STOP=set("the and for with from into this that your our their about company home services service contact more india global international website official page read learn get best top leading solutions solution logistics".split())
TOKEN_RE=re.compile(r"[A-Za-z][A-Za-z0-9+&/-]{2,}")

def _search(query, limit=8):
    try:
        r=httpx.get("https://html.duckduckgo.com/html/",params={"q":query},headers={"User-Agent":"GEORUSH-Keyword-Intelligence/1.0"},timeout=15,follow_redirects=True)
        r.raise_for_status(); soup=BeautifulSoup(r.text,"lxml")
        out=[]
        for x in soup.select(".result")[:limit]:
            a=x.select_one("a.result__a"); sn=x.select_one(".result__snippet")
            if a: out.append({"title":a.get_text(" ",strip=True),"url":a.get("href",""),"snippet":sn.get_text(" ",strip=True) if sn else ""})
        return out
    except Exception as e:
        return [{"error":str(e)}]

def _phrases(text, min_n=2, max_n=4):
    toks=[x.lower() for x in TOKEN_RE.findall(text or "") if x.lower() not in STOP]
    out=[]
    for n in range(max_n,min_n-1,-1):
        for i in range(len(toks)-n+1):
            p=" ".join(toks[i:i+n])
            if any(len(x)<3 for x in p.split()): continue
            out.append(p)
    return out

def build_keyword_intelligence(target, crawl_results=None, seed_keywords=None, limit=40):
    crawl_results=crawl_results or []
    seed_keywords=[str(x).strip().lower() for x in (seed_keywords or []) if str(x).strip()]
    pages=[]
    for p in crawl_results[:30]:
        pages.append({"url":p.get("url",""),"title":p.get("title",""),"h1":p.get("h1",""),"words":p.get("word_count",0)})
    root=pages[0] if pages else {}
    seed_text=" ".join(seed_keywords+[root.get("title","") ,root.get("h1","")])
    base_phrases=_phrases(seed_text)
    queries=[]
    for p in seed_keywords[:8]+base_phrases[:8]:
        if p not in queries: queries.append(p)
    if not queries:
        queries=[target.replace("https://","").replace("http://","").split("/")[0]]
    serp=[]
    for q in queries[:8]: serp.extend(_search(q,6))
    counts=Counter(); evidence=defaultdict(list); page_map=defaultdict(set)
    for kw in seed_keywords: counts[kw]+=3; evidence[kw].append("seed")
    for p in pages:
        text=" ".join([p.get("title","") or "",p.get("h1","") or ""])
        for kw in set(_phrases(text)):
            counts[kw]+=2; evidence[kw].append("site"); page_map[kw].add(p.get("url",""))
    for s in serp:
        if s.get("error"): continue
        text=" ".join([s.get("title","") or "",s.get("snippet","") or ""])
        for kw in set(_phrases(text)):
            counts[kw]+=1; evidence[kw].append("serp")
    rows=[]
    for kw,c in counts.most_common():
        if len(kw)<5 or kw in STOP: continue
        intent=classify_intent(kw)
        src=set(evidence[kw]);
        relevance=min(100,30+c*8+(20 if "site" in src else 0)+(20 if "serp" in src else 0))
        rows.append({"keyword":kw,"intent":intent,"evidence_score":relevance,"sources":sorted(src),
                     "serp_mentions":evidence[kw].count("serp"),"mapped_pages":sorted(x for x in page_map[kw] if x),
                     "data_type":"evidence-based; no search-volume or rank claim"})
        if len(rows)>=limit: break
    themes=[]
    for intent in ["Commercial","Transactional","Informational","Navigational"]:
        vals=[x for x in rows if x["intent"]==intent][:8]
        if vals: themes.append({"intent":intent,"keywords":[x["keyword"] for x in vals]})
    return {"target":target,"site_title":root.get("title","") or "","seed_keywords":seed_keywords,
            "search_records":len([x for x in serp if not x.get("error")]),"keywords":rows,"themes":themes,
            "limitations":["Search volume, CPC and actual Google rankings are not available unless GSC/another provider is connected."],
            "pages_analyzed":len(pages)}
