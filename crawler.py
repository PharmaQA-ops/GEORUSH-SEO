import re
import time
import urllib.parse
import urllib.robotparser
from collections import deque
from typing import Dict, List, Set
import httpx
from bs4 import BeautifulSoup

ISSUES = {
    "HTTP_ERROR", "MISSING_TITLE", "TITLE_TOO_LONG", "MISSING_DESCRIPTION",
    "DESCRIPTION_TOO_LONG", "MISSING_H1", "MULTIPLE_H1", "MISSING_CANONICAL",
    "NOINDEX", "THIN_CONTENT", "MISSING_IMAGE_ALT", "REDIRECT", "CRAWL_ERROR"
}

def normalize_url(url: str) -> str:
    p = urllib.parse.urlsplit(url)
    scheme = p.scheme or "https"
    host = p.netloc.lower()
    path = p.path or "/"
    if path != "/" and path.endswith("/"):
        path = path[:-1]
    return urllib.parse.urlunsplit((scheme, host, path, p.query, ""))

def is_internal(url: str, root_host: str) -> bool:
    try:
        return urllib.parse.urlsplit(url).netloc.lower() == root_host
    except Exception:
        return False

def parse_page(url: str, html: str) -> Dict:
    soup = BeautifulSoup(html, "lxml")
    title = soup.title.get_text(" ", strip=True) if soup.title else ""
    desc_tag = soup.find("meta", attrs={"name": re.compile("^description$", re.I)})
    description = desc_tag.get("content", "").strip() if desc_tag else ""
    h1s = [x.get_text(" ", strip=True) for x in soup.find_all("h1")]
    canonical_tag = soup.find("link", rel=lambda v: v and "canonical" in v)
    canonical = canonical_tag.get("href", "").strip() if canonical_tag else ""
    robots_tag = soup.find("meta", attrs={"name": re.compile("^robots$", re.I)})
    robots = robots_tag.get("content", "").lower() if robots_tag else ""
    text = soup.get_text(" ", strip=True)
    words = len(text.split())
    images = soup.find_all("img")
    missing_alt = sum(1 for img in images if not img.get("alt"))
    links = []
    internal = external = 0
    for a in soup.find_all("a", href=True):
        href = urllib.parse.urljoin(url, a["href"])
        if href.startswith(("http://", "https://")):
            links.append(href)
            if is_internal(href, urllib.parse.urlsplit(url).netloc.lower()):
                internal += 1
            else:
                external += 1

    issues = []
    if not title: issues.append("MISSING_TITLE")
    if len(title) > 60: issues.append("TITLE_TOO_LONG")
    if not description: issues.append("MISSING_DESCRIPTION")
    if len(description) > 160: issues.append("DESCRIPTION_TOO_LONG")
    if len(h1s) == 0: issues.append("MISSING_H1")
    if len(h1s) > 1: issues.append("MULTIPLE_H1")
    if not canonical: issues.append("MISSING_CANONICAL")
    if "noindex" in robots: issues.append("NOINDEX")
    if words < 300: issues.append("THIN_CONTENT")
    if missing_alt: issues.append("MISSING_IMAGE_ALT")

    return {
        "url": url, "title": title, "description": description,
        "h1": h1s[0] if h1s else "", "h1_count": len(h1s),
        "canonical": canonical, "robots": robots, "word_count": words,
        "image_count": len(images), "missing_alt": missing_alt,
        "internal_links": internal, "external_links": external,
        "links": links, "issues": issues
    }

def crawl(root_url: str, max_pages: int = 25) -> Dict:
    root_url = normalize_url(root_url)
    parsed = urllib.parse.urlsplit(root_url)
    host = parsed.netloc.lower()

    rp = urllib.robotparser.RobotFileParser()
    robots_url = urllib.parse.urlunsplit((parsed.scheme, host, "/robots.txt", "", ""))
    robots_available = False
    try:
        rp.set_url(robots_url)
        rp.read()
        robots_available = True
    except Exception:
        pass

    queue = deque([root_url])
    seen: Set[str] = set()
    results: List[Dict] = []

    with httpx.Client(follow_redirects=True, timeout=15, headers={"User-Agent": "GEORUSH-SEO-Crawler/0.2"}) as client:
        while queue and len(results) < max_pages:
            url = queue.popleft()
            url = normalize_url(url)
            if url in seen or not is_internal(url, host):
                continue
            seen.add(url)

            if robots_available and not rp.can_fetch("GEORUSH-SEO-Crawler", url):
                continue

            start = time.perf_counter()
            try:
                response = client.get(url)
                elapsed = round((time.perf_counter() - start) * 1000)
                final_url = normalize_url(str(response.url))
                item = {
                    "url": url,
                    "status_code": response.status_code,
                    "response_time_ms": elapsed,
                    "redirect": final_url != url,
                }
                if response.is_success and "text/html" in response.headers.get("content-type", "").lower():
                    item.update(parse_page(final_url, response.text))
                    if item["redirect"]:
                        item["issues"].append("REDIRECT")
                    for link in item.pop("links", []):
                        n = normalize_url(link)
                        if is_internal(n, host) and n not in seen and len(seen) < max_pages * 4:
                            queue.append(n)
                else:
                    item.update({
                        "title": "", "description": "", "h1": "", "h1_count": 0,
                        "canonical": "", "robots": "", "word_count": 0,
                        "image_count": 0, "missing_alt": 0, "internal_links": 0,
                        "external_links": 0, "issues": ["HTTP_ERROR"]
                    })
                results.append(item)
            except Exception as exc:
                results.append({
                    "url": url, "status_code": 0, "response_time_ms": 0,
                    "redirect": False, "title": "", "description": "", "h1": "",
                    "h1_count": 0, "canonical": "", "robots": "", "word_count": 0,
                    "image_count": 0, "missing_alt": 0, "internal_links": 0,
                    "external_links": 0, "issues": ["CRAWL_ERROR"], "error": str(exc)
                })

    issue_count = sum(len(x.get("issues", [])) for x in results)
    health = max(0, 100 - min(100, issue_count * 5))
    return {
        "root_url": root_url,
        "robots_available": robots_available,
        "sitemap_count": 0,
        "pages": len(results),
        "health": health,
        "issues": issue_count,
        "results": results
    }
