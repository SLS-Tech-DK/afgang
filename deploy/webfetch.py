"""
SLS Tech · Afgang — let web-fetch til grounded analyser.
Henter en offentlig side, stripper HTML til ren tekst, trunkeret.
Bruges af konkurrentanalyse (tung tier). Ingen tredjeparts-afhængigheder.
"""
from __future__ import annotations
import re, urllib.request, urllib.error

_UA = "Mozilla/5.0 (compatible; SLSTechBot/1.0; +https://slstech.dk)"


def _strip_html(html: str) -> str:
    html = re.sub(r"(?is)<(script|style|noscript|svg)[^>]*>.*?</\1>", " ", html)
    html = re.sub(r"(?is)<!--.*?-->", " ", html)
    text = re.sub(r"(?is)<[^>]+>", " ", html)
    text = re.sub(r"&nbsp;", " ", text)
    text = re.sub(r"&amp;", "&", text)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n\s*\n\s*", "\n\n", text)
    return text.strip()


def fetch_text(url: str, max_chars: int = 6000, timeout: int = 15) -> dict:
    """Hent én URL → {url, ok, text|error}. Normaliserer manglende scheme."""
    if not url:
        return {"url": url, "ok": False, "error": "tom URL"}
    if not url.startswith(("http://", "https://")):
        url = "https://" + url
    try:
        req = urllib.request.Request(url, headers={"User-Agent": _UA})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            raw = r.read(400_000).decode("utf-8", errors="ignore")
        text = _strip_html(raw)[:max_chars]
        return {"url": url, "ok": True, "text": text}
    except Exception as e:
        return {"url": url, "ok": False, "error": f"{type(e).__name__}: {e}"}
