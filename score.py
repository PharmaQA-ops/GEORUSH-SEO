def calculate_score(results):
    pages = len(results)
    if not pages:
        return {"total": 0, "grade": "Critical", "categories": {}}

    def rate(pred):
        bad = sum(1 for p in results if pred(p))
        return round(max(0, 100 - (bad / pages) * 100), 1)

    technical = rate(lambda p: any(i in p.get("issues",[]) for i in
        ["HTTP_ERROR","CRAWL_ERROR","BROKEN_INTERNAL_LINK","REDIRECT","REDIRECT_CHAIN"]))
    indexability = rate(lambda p: any(i in p.get("issues",[]) for i in
        ["NOINDEX","CANONICAL_MISMATCH","MISSING_CANONICAL","ORPHAN_PAGE"]))
    onpage = rate(lambda p: any(i in p.get("issues",[]) for i in
        ["MISSING_TITLE","TITLE_TOO_LONG","DUPLICATE_TITLE","MISSING_DESCRIPTION",
         "DESCRIPTION_TOO_LONG","DUPLICATE_DESCRIPTION","MISSING_H1","MULTIPLE_H1"]))
    content = rate(lambda p: any(i in p.get("issues",[]) for i in ["THIN_CONTENT","MISSING_IMAGE_ALT"]))
    linking = rate(lambda p: p.get("internal_links",0) == 0)
    performance = rate(lambda p: p.get("response_time_ms",0) > 2000)

    cats = {
        "Technical SEO": technical,
        "Indexability": indexability,
        "On-Page SEO": onpage,
        "Content Quality": content,
        "Internal Linking": linking,
        "Performance": performance,
    }
    weights = {"Technical SEO":.30,"Indexability":.20,"On-Page SEO":.20,
               "Content Quality":.15,"Internal Linking":.10,"Performance":.05}
    total = round(sum(cats[k]*weights[k] for k in cats),1)
    grade = "Excellent" if total>=90 else "Good" if total>=80 else "Needs Improvement" if total>=70 else "Poor" if total>=50 else "Critical"
    return {"total":total,"grade":grade,"categories":cats}
