"""
SLS Tech · Afgang — Review-/omdømme-analyse
-------------------------------------------
Input: reviews-CSV (rating [+ tekst] [+ produkt]).
Output: rating-fordeling, gennemsnit, tema-frekvens (hvad klages der over),
og hvilke temaer der optræder mest i lave anmeldelser (koster salg).
Nuanceret tema-sammenfatning = Gemini (interface). Her tælles deterministisk.
"""
from __future__ import annotations
import re, csv, io
from collections import Counter, defaultdict
from salgsanalyse import _to_float


def _round(x, n=2):
    return round(x + 0.0, n)


# Danske + engelske klage-/ros-temaer (delstrengs-match, udvidbart)
THEMES = {
    "levering": ["levering", "leverance", "fragt", "pakke", "forsinke", "shipping", "delivery", "sen "],
    "kvalitet": ["kvalitet", "dårlig", "daarlig", "billig", "gik i stykker", "defekt", "quality", "broke"],
    "pris": ["pris", "dyr", "dyrt", "penge værd", "expensive", "overpriced"],
    "kundeservice": ["service", "svar", "kontakt", "hjælp", "hjaelp", "support", "rude", "uforskammet"],
    "størrelse/pasform": ["størrelse", "stoerrelse", "passer", "pasform", "for lille", "for stor", "size", "fit"],
    "retur": ["retur", "bytte", "refund", "returnere", "pengene tilbage"],
}


def _detect(headers):
    def find(cands):
        for h in headers:
            hl = re.sub(r"[^a-z0-9]", "", h.lower())
            if any(re.sub(r"[^a-z0-9]", "", c) in hl for c in cands):
                return h
        return None
    return {"rating": find(["rating", "stjerne", "score", "karakter", "vurdering", "stars"]),
            "text": find(["tekst", "review", "kommentar", "anmeldelse", "body", "text", "comment"]),
            "product": find(["produkt", "vare", "product", "item"])}


def _themes_in(text):
    tl = (text or "").lower()
    return [name for name, kws in THEMES.items() if any(k in tl for k in kws)]


def analyze(csv_text: str, low_threshold: float = 3.0) -> dict:
    try:
        delim = csv.Sniffer().sniff(csv_text[:2048], delimiters=",;\t|").delimiter
    except csv.Error:
        delim = ","
    reader = csv.DictReader(io.StringIO(csv_text), delimiter=delim)
    cols = _detect(reader.fieldnames or [])
    rows = list(reader)
    ratings = []
    theme_counts = Counter()
    low_theme_counts = Counter()
    dist = Counter()
    for r in rows:
        rat = _to_float(r.get(cols["rating"])) if cols["rating"] else None
        text = r.get(cols["text"]) if cols["text"] else ""
        if rat is not None:
            ratings.append(rat)
            dist[int(round(rat))] += 1
        th = _themes_in(text)
        for t in th:
            theme_counts[t] += 1
            if rat is not None and rat <= low_threshold:
                low_theme_counts[t] += 1
    if not ratings and not theme_counts:
        return {"error": "Kunne ikke finde rating eller review-tekst i CSV'en.",
                "columns_found": reader.fieldnames}
    avg = _round(sum(ratings) / len(ratings), 2) if ratings else None
    low_share = _round(sum(1 for r in ratings if r <= low_threshold) / len(ratings) * 100, 1) if ratings else None
    return {
        "meta": {"columns": cols, "reviews": len(rows), "avg_rating": avg,
                 "low_rating_share_pct": low_share, "low_threshold": low_threshold},
        "rating_distribution": dict(sorted(dist.items())),
        "themes": theme_counts.most_common(),
        "themes_in_low_reviews": low_theme_counts.most_common(),
    }
