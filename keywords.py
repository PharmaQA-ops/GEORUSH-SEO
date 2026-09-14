import re
from collections import Counter

INTENT_RULES = {
    "Transactional": [r"\bbuy\b",r"\bprice\b",r"\bquote\b",r"\border\b",r"\bservice\b",r"\bhire\b"],
    "Commercial": [r"\bbest\b",r"\btop\b",r"\breview\b",r"\bcompare\b",r"\bvs\b",r"\bcompany\b"],
    "Navigational": [r"\blogin\b",r"\bcontact\b",r"\bwebsite\b",r"\baddress\b"],
    "Informational": [r"\bhow\b",r"\bwhat\b",r"\bwhy\b",r"\bguide\b",r"\bmeaning\b",r"\btutorial\b"]
}

def classify_intent(keyword):
    k=keyword.lower()
    for intent, rules in INTENT_RULES.items():
        if any(re.search(rule,k) for rule in rules):
            return intent
    return "Informational"

def opportunity_score(row):
    clicks=float(row.get("clicks",0) or 0)
    impressions=float(row.get("impressions",0) or 0)
    ctr=float(row.get("ctr",0) or 0)
    position=float(row.get("position",100) or 100)
    # High impressions + positions 4-20 + low CTR = practical optimization opportunity.
    score=0
    score += min(40, impressions/100)
    if 4 <= position <= 20: score += 35
    elif position <= 30: score += 20
    score += min(25, max(0, (0.08-ctr)*300))
    return round(min(100,score),1)

def normalize_gsc_rows(data):
    rows=[]
    for r in data.get("rows",[]):
        keys=r.get("keys",[])
        keyword=keys[0] if keys else ""
        page=keys[1] if len(keys)>1 else ""
        item={"keyword":keyword,"page":page,
              "clicks":r.get("clicks",0),"impressions":r.get("impressions",0),
              "ctr":r.get("ctr",0),"position":r.get("position",0)}
        item["intent"]=classify_intent(keyword)
        item["opportunity_score"]=opportunity_score(item)
        rows.append(item)
    return rows

def summarize(rows):
    return {
        "keywords":len(rows),
        "clicks":round(sum(float(x.get("clicks",0)) for x in rows),2),
        "impressions":round(sum(float(x.get("impressions",0)) for x in rows),2),
        "avg_position":round(sum(float(x.get("position",0)) for x in rows)/len(rows),2) if rows else 0,
        "intent_distribution":dict(Counter(x["intent"] for x in rows)),
        "opportunities":sorted(rows,key=lambda x:x["opportunity_score"],reverse=True)[:20]
    }
