#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
afgang Hjemmeside-analyse — fetch (crawler).

Henter en hjemmesides forside + undersider samt robots.txt / sitemap.xml / llms.txt,
og returnerer en SiteData-dict som analyze.py forstår.

VIGTIGT: Dette trin laver netværkskald og skal køre på Cloud Run (afgangs/kundens egress)
— IKKE i cowork-containeren, hvor web-fetch er begrænset. Derfor er netværksdelen isoleret
her og importeres ikke af analyze.py (som er ren, netværksfri og kan testes lokalt).

Brug (på Cloud Run):
    from fetch_site import fetch_site
    data = fetch_site("https://eksempel.dk", name="Eksempel", max_pages=20)
    json.dump(data, open("site_data.json","w"), ensure_ascii=False)
"""
from __future__ import annotations
import re
from urllib.parse import urljoin, urlparse

USER_AGENT = "afgang-hjemmeside-analyse/1.0 (+https://slstech.dk)"
TIMEOUT = 15


def _norm(base: str) -> str:
    base = base.strip()
    if not base.startswith(("http://", "https://")):
        base = "https://" + base
    return base.rstrip("/")


def _get(session, url: str):
    """Return (status_code, text) or (None, '') on failure. Never raises."""
    try:
        r = session.get(url, timeout=TIMEOUT, allow_redirects=True)
        ctype = r.headers.get("content-type", "")
        text = r.text if ("text" in ctype or "xml" in ctype or "json" in ctype or not ctype) else ""
        return r.status_code, text
    except Exception:
        return None, ""


def _urls_from_sitemap(xml: str, base: str, limit: int) -> list[str]:
    if not xml:
        return []
    locs = re.findall(r"<loc>\s*([^<\s]+)\s*</loc>", xml, flags=re.I)
    host = urlparse(base).netloc
    out = []
    for u in locs:
        u = u.strip()
        if urlparse(u).netloc == host and not u.lower().endswith((".xml", ".jpg", ".png", ".pdf")):
            out.append(u.rstrip("/"))
        if len(out) >= limit:
            break
    return out


def _urls_from_links(html: str, base: str, limit: int) -> list[str]:
    host = urlparse(base).netloc
    out = []
    for href in re.findall(r'href=["\']([^"\']+)["\']', html or "", flags=re.I):
        u = urljoin(base + "/", href).split("#")[0].rstrip("/")
        if urlparse(u).netloc == host and u != base and not u.lower().endswith(
            (".jpg", ".png", ".pdf", ".zip", ".css", ".js", ".ico", ".svg")
        ):
            if u not in out:
                out.append(u)
        if len(out) >= limit:
            break
    return out


def fetch_site(url: str, name: str = "", type: str = "", tech: str = "", max_pages: int = 20) -> dict:
    """Fetch a site into a SiteData dict. Runs only where outbound HTTP is allowed (Cloud Run)."""
    import requests  # imported lazily so analyze.py stays import-safe without network deps
    base = _norm(url)
    session = requests.Session()
    session.headers["User-Agent"] = USER_AGENT

    _, robots = _get(session, base + "/robots.txt")
    _, sitemap = _get(session, base + "/sitemap.xml")
    if not sitemap:
        _, sitemap = _get(session, base + "/sitemap_index.xml")
    _, llms = _get(session, base + "/llms.txt")

    status_front, front_html = _get(session, base + "/")

    urls = _urls_from_sitemap(sitemap, base, max_pages)
    if not urls:
        urls = _urls_from_links(front_html, base, max_pages)
    # always include the front page first, de-duplicated
    ordered = [base] + [u for u in urls if u != base]
    ordered = ordered[:max_pages]

    pages = []
    for u in ordered:
        if u == base:
            code, h = status_front, front_html
        else:
            code, h = _get(session, u)
        if h:
            pages.append({"url": u, "status": code, "html": h})

    return {
        "base_url": base,
        "name": name or urlparse(base).netloc,
        "type": type,
        "tech": tech,
        "https": base.startswith("https://"),
        "robots_txt": robots or None,
        "sitemap_xml": sitemap or None,
        "llms_txt": llms or None,
        "pages": pages,
    }


if __name__ == "__main__":
    import sys, json
    d = fetch_site(sys.argv[1], name=sys.argv[2] if len(sys.argv) > 2 else "")
    d_light = {**d, "pages": [{"url": p["url"], "status": p["status"], "bytes": len(p["html"])} for p in d["pages"]]}
    print(json.dumps(d_light, ensure_ascii=False, indent=2))
