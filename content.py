import re
from collections import Counter

STOPWORDS=set("""the a an and or but if then for of to in on at by with from is are was were be this that these those it its as into about your our their you we they he she them his her not no do does did can could should would will just than too very""".split())

def analyze_text(text, keyword=""):
    words=re.findall(r"[A-Za-z0-9][A-Za-z0-9'-]*", text.lower())
    clean=[w for w in words if w not in STOPWORDS]
    counts=Counter(clean)
    total=len(words)
    keyword_terms=re.findall(r"[A-Za-z0-9]+", keyword.lower())
    phrase_count=text.lower().count(keyword.lower()) if keyword else 0
    return {
        "word_count":total,
        "unique_words":len(set(clean)),
        "top_terms":[{"term":w,"count":c} for w,c in counts.most_common(20)],
        "keyword":keyword,
        "keyword_occurrences":phrase_count,
        "keyword_density":round((phrase_count/max(1,total))*100,2) if keyword else 0,
        "readability_hint":"Shorter sentences and clearer headings are generally preferable." if total else ""
    }

def content_issues(page):
    issues=[]
    title=page.get("title","")
    desc=page.get("description","")
    words=page.get("word_count",0)
    if not title: issues.append("MISSING_TITLE")
    if not desc: issues.append("MISSING_DESCRIPTION")
    if words<300: issues.append("THIN_CONTENT")
    if page.get("h1_count",0)==0: issues.append("MISSING_H1")
    if page.get("h1_count",0)>1: issues.append("MULTIPLE_H1")
    return issues
