"""
SLS Tech · Afgang — Søgeords-gap fra intern søgelog
---------------------------------------------------
Input: intern site-search-log-CSV (søgeterm, antal søgninger, [antal resultater
eller fundet-flag]). Output: søgetermer med mange søgninger men ingen/få
resultater = manglende produkter = tabt salg. Prioriteret liste.
Deterministisk. 100% på kundens egen data — svær at kopiere.
"""
from __future__ import annotations
import re, csv, io
from collections import defaultdict
from salgsanalyse import _to_float


def _round(x, n=0):
    return round(x + 0.0, n)


def _detect(headers):
    def find(cands):
        for h in headers:
            hl = re.sub(r"[^a-z0-9]", "", h.lower())
            if any(re.sub(r"[^a-z0-9]", "", c) in hl for c in cands):
                return h
        return None
    return {"term": find(["soegeterm", "søgeterm", "term", "query", "søgning", "soegning", "keyword", "search"]),
            "count": find(["antal", "count", "soegninger", "søgninger", "searches", "volume", "haits", "hits"]),
            "results": find(["resultater", "results", "hits", "antalresultater", "found", "fundet", "matches"])}


def analyze(csv_text: str) -> dict:
    try:
        delim = csv.Sniffer().sniff(csv_text[:2048], delimiters=",;\t|").delimiter
    except csv.Error:
        delim = ","
    reader = csv.DictReader(io.StringIO(csv_text), delimiter=delim)
    cols = _detect(reader.fieldnames or [])
    if not cols["term"]:
        return {"error": "Søgelog-CSV mangler en søgeterm-kolonne.",
                "columns_found": reader.fieldnames}
    agg = defaultdict(lambda: {"count": 0.0, "results_sum": 0.0, "rows": 0})
    for r in reader:
        term = (r.get(cols["term"]) or "").strip().lower()
        if not term:
            continue
        cnt = _to_float(r.get(cols["count"])) if cols["count"] else 1
        cnt = cnt if cnt is not None else 1
        res = _to_float(r.get(cols["results"])) if cols["results"] else None
        a = agg[term]
        a["count"] += cnt
        a["rows"] += 1
        if res is not None:
            a["results_sum"] += res
    terms = []
    for term, a in agg.items():
        avg_results = (a["results_sum"] / a["rows"]) if (cols["results"] and a["rows"]) else None
        terms.append({"term": term, "searches": _round(a["count"]),
                      "avg_results": _round(avg_results, 1) if avg_results is not None else None})
    # gap = mange søgninger, ingen/få resultater (hvis results-kolonne findes);
    # ellers bare top-søgninger (kunden tjekker selv hvad der mangler).
    if cols["results"]:
        gaps = [t for t in terms if (t["avg_results"] is not None and t["avg_results"] < 1)]
        gaps.sort(key=lambda x: x["searches"], reverse=True)
        note = "Termer med mange søgninger og ingen resultater = manglende produkter/kategorier."
    else:
        gaps = sorted(terms, key=lambda x: x["searches"], reverse=True)
        note = "Ingen resultat-kolonne — viser top-søgninger. Tilføj 'antal resultater' for at finde ægte gaps."
    return {
        "meta": {"columns": cols, "distinct_terms": len(terms), "has_results_column": bool(cols["results"])},
        "note": note,
        "gaps": gaps[:30],
        "top_searches": sorted(terms, key=lambda x: x["searches"], reverse=True)[:20],
    }
