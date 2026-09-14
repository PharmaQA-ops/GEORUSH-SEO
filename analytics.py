from datetime import date, timedelta

def analytics_summary(gsc_rows=None):
    rows=gsc_rows or []
    clicks=sum(float(r.get("clicks",0) or 0) for r in rows)
    impressions=sum(float(r.get("impressions",0) or 0) for r in rows)
    ctr=(clicks/impressions) if impressions else 0
    positions=[float(r.get("position",0) or 0) for r in rows if r.get("position")]
    position=sum(positions)/len(positions) if positions else 0
    return {
        "date_range":{"start":(date.today()-timedelta(days=28)).isoformat(),"end":date.today().isoformat()},
        "sessions":0,
        "users":0,
        "engagement_rate":0,
        "conversions":0,
        "search_clicks":round(clicks,2),
        "search_impressions":round(impressions,2),
        "search_ctr":round(ctr,4),
        "average_position":round(position,2),
        "source":"GSC-ready"
    }
