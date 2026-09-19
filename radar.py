
import os, urllib.parse, httpx

RADAR_BASE="https://api.cloudflare.com/client/v4/radar"

def public_scan_url(url):
    return "https://radar.cloudflare.com/scan?url="+urllib.parse.quote(url,safe="")

def scan_url(url):
    """Optional authenticated Cloudflare URL Scanner integration.
    Without credentials, returns a Radar link and explains what must be configured.
    """
    token=os.getenv("CLOUDFLARE_API_TOKEN","").strip()
    account=os.getenv("CLOUDFLARE_ACCOUNT_ID","").strip()
    if not token or not account:
        return {"configured":False,"url":url,"radar_url":public_scan_url(url),
                "message":"Cloudflare URL Scanner API credentials are not configured."}
    headers={"Authorization":f"Bearer {token}","Content-Type":"application/json"}
    try:
        with httpx.Client(timeout=20) as c:
            r=c.post(f"https://api.cloudflare.com/client/v4/accounts/{account}/urlscanner/v2/scan",
                     headers=headers,json={"url":url,"visibility":"Unlisted"})
            r.raise_for_status()
            data=r.json().get("result",{})
        return {"configured":True,"url":url,"scan":data,"radar_url":public_scan_url(url)}
    except Exception as e:
        return {"configured":True,"url":url,"radar_url":public_scan_url(url),"error":str(e)}

def get_result(scan_id):
    token=os.getenv("CLOUDFLARE_API_TOKEN","").strip()
    account=os.getenv("CLOUDFLARE_ACCOUNT_ID","").strip()
    if not token or not account or not scan_id:
        return {"configured":False}
    try:
        with httpx.Client(timeout=20) as c:
            r=c.get(f"https://api.cloudflare.com/client/v4/accounts/{account}/urlscanner/v2/result/{scan_id}",
                    headers={"Authorization":f"Bearer {token}"})
            if r.status_code==404: return {"configured":True,"status":"InProgress"}
            r.raise_for_status()
            return {"configured":True,"status":"Finished","result":r.json().get("result",r.json())}
    except Exception as e:
        return {"configured":True,"error":str(e)}

def radar_summary(url, scan=None):
    out={"url":url,"radar_url":public_scan_url(url),"configured":bool(os.getenv("CLOUDFLARE_API_TOKEN") and os.getenv("CLOUDFLARE_ACCOUNT_ID"))}
    if scan:
        result=scan.get("result",scan)
        page=result.get("page",{}) if isinstance(result,dict) else {}
        meta=result.get("meta",{}) if isinstance(result,dict) else {}
        proc=meta.get("processors",{}) if isinstance(meta,dict) else {}
        out.update({
            "final_url":page.get("url"),
            "country":page.get("country"),
            "asn":page.get("asn"),
            "radar_rank":proc.get("radarRank"),
            "technologies":proc.get("wappa"),
            "phishing":proc.get("phishing"),
            "malicious":(result.get("verdicts",{}).get("overall",{}) or {}).get("malicious"),
            "performance":result.get("data",{}).get("performance",{}),
            "requests":len(result.get("data",{}).get("requests",[]) or []),
        })
    return out
