"""
SLS Tech · Afgang — Kundeanalyse-motor (delelement af Butiksrøntgen)
-------------------------------------------------------------------
Deterministisk. Genbruger CSV-genkendelseslaget fra salgsanalyse.
Kræver kunde-kolonne. Beregner:
  - kunde-livstidsværdi (CLV): samlet omsætning pr. kunde, rangeret
  - RFM-lite: recency (dage siden sidste køb), frequency (antal ordrer), monetary
  - churn-signal: kunder hvis sidste køb er ældre end en tærskel
  - segmenter: engangskøbere vs. gengangere + deres omsætningsandel

Mangler kunde-kolonne → degraderer og siger det. Opfinder aldrig kunder.
"""

from __future__ import annotations
import json
from collections import defaultdict
from datetime import timedelta
from statistics import median
from salgsanalyse import load_lines, _round


def _by_customer(lines):
    rev = defaultdict(float)
    orders = defaultdict(set)
    last = {}
    for l in lines:
        c = l["customer"]
        if not c:
            continue
        rev[c] += l["revenue"]
        orders[c].add(l["order_id"])
        if l["date"] and (c not in last or l["date"] > last[c]):
            last[c] = l["date"]
    return rev, orders, last


def clv(rev, orders, top=20):
    out = [{"customer": c, "revenue": _round(v), "orders": len(orders[c]),
            "avg_order_value": _round(v / len(orders[c])) if orders[c] else 0}
           for c, v in rev.items()]
    out.sort(key=lambda x: x["revenue"], reverse=True)
    return out[:top]


def rfm(rev, orders, last, ref_date, top=20):
    out = []
    for c in rev:
        recency = (ref_date - last[c]).days if (ref_date and c in last) else None
        out.append({"customer": c, "recency_days": recency,
                    "frequency_orders": len(orders[c]), "monetary": _round(rev[c])})
    out.sort(key=lambda x: x["monetary"], reverse=True)
    return out[:top]


def churn_signal(last, ref_date, days=120):
    if not ref_date:
        return []
    cutoff = ref_date - timedelta(days=days)
    out = [{"customer": c, "last_purchase": d, "days_since": (ref_date - d).days}
           for c, d in last.items() if d < cutoff]
    out.sort(key=lambda x: x["days_since"], reverse=True)
    return out


def segments(rev, orders):
    one_time = [c for c in orders if len(orders[c]) == 1]
    repeat = [c for c in orders if len(orders[c]) >= 2]
    rev_one = sum(rev[c] for c in one_time)
    rev_rep = sum(rev[c] for c in repeat)
    total = rev_one + rev_rep
    return {
        "one_time_customers": len(one_time),
        "repeat_customers": len(repeat),
        "repeat_share_pct": _round(len(repeat) / (len(one_time)+len(repeat)) * 100, 1) if (one_time or repeat) else 0,
        "revenue_from_repeat_pct": _round(rev_rep / total * 100, 1) if total else 0,
    }


def rfm_segments(rev, orders, last, ref_date):
    """Ægte RFM: quintil-score (1-5) for Recency, Frequency, Monetary → segmenter.
    Returnerer segment-fordeling + eksempel-kunder pr. segment."""
    custs = list(rev.keys())
    if not custs or not ref_date:
        return {"note": "Kræver kunde- og dato-data for RFM-segmentering."}
    rec = {c: (ref_date - last[c]).days if c in last else 10**6 for c in custs}
    freq = {c: len(orders[c]) for c in custs}
    mon = {c: rev[c] for c in custs}

    def score(vals, reverse):
        # reverse=True: lav værdi = høj score (recency: nyligt køb = bedst)
        order = sorted(vals, key=lambda c: vals[c], reverse=not reverse)
        n = len(order)
        out = {}
        for i, c in enumerate(order):
            out[c] = 5 - min(4, int(i * 5 / n)) if n else 3
        return out

    R = score(rec, reverse=True)   # lav recency-dage = høj score
    F = score(freq, reverse=False)
    M = score(mon, reverse=False)

    def seg(c):
        r, f, m = R[c], F[c], M[c]
        fm = (f + m) / 2
        if r >= 4 and fm >= 4: return "Champions"
        if r >= 3 and fm >= 3: return "Loyale"
        if r >= 4 and fm <= 2: return "Nye/lovende"
        if r <= 2 and fm >= 4: return "Ved at miste (høj værdi)"
        if r <= 2 and fm >= 3: return "At-risk"
        if r <= 2 and fm <= 2: return "Tabt/dvale"
        return "Skal plejes"

    seg_of = {c: seg(c) for c in custs}
    from collections import defaultdict as _dd
    buckets = _dd(list)
    for c in custs:
        buckets[seg_of[c]].append(c)
    dist = []
    for name, cs in buckets.items():
        cs_sorted = sorted(cs, key=lambda c: mon[c], reverse=True)
        dist.append({
            "segment": name,
            "customers": len(cs),
            "revenue": _round(sum(mon[c] for c in cs)),
            "examples": [{"customer": c, "recency_days": rec[c], "orders": freq[c],
                          "monetary": _round(mon[c])} for c in cs_sorted[:3]],
        })
    dist.sort(key=lambda x: x["revenue"], reverse=True)
    return {"by_segment": dist,
            "note": "RFM-quintiler (1-5) pr. kunde vejet til segmenter. Handl først på Champions (plej), Ved-at-miste (vind tilbage) og At-risk."}


def analyze(csv_text: str, churn_days: int = 120) -> dict:
    lines, mapping = load_lines(csv_text)
    if not lines:
        return {"error": "Ingen brugbare salgslinjer fundet.", "column_mapping": mapping}
    if not any(l["customer"] for l in lines):
        return {"error": "Ingen kunde-kolonne fundet — kundeanalyse kræver kunde-id/email.",
                "column_mapping": mapping}
    rev, orders, last = _by_customer(lines)
    dates = [l["date"] for l in lines if l["date"]]
    ref = max(dates) if dates else None
    warnings = [] if dates else ["Ingen dato-kolonne — recency og churn kan ikke beregnes."]
    return {
        "meta": {"column_mapping": mapping, "rows_used": len(lines),
                 "distinct_customers": len(rev), "reference_date": ref, "warnings": warnings},
        "clv": clv(rev, orders),
        "rfm": rfm(rev, orders, last, ref),
        "churn_signal": churn_signal(last, ref, churn_days),
        "segments": segments(rev, orders),
        "rfm_segments": rfm_segments(rev, orders, last, ref),
    }


if __name__ == "__main__":
    import sys
    print(json.dumps(analyze(open(sys.argv[1], encoding="utf-8").read()),
                     ensure_ascii=False, indent=2, default=str))
