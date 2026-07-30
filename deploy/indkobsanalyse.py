"""
SLS Tech · Afgang — Indkøbsanalyse-motor (delelement af Butiksrøntgen)
---------------------------------------------------------------------
Deterministisk beregningskerne. Genbruger CSV-genkendelseslaget fra
salgsanalyse. Producerer:
  - salgshastighed pr. produkt (enheder/dag) + rangering
  - genbestillingsliste (fast movers der skal holdes på lager)
  - genkøbsinterval pr. produkt (hvor tit samme kunde køber igen)
  - koncentration (hvor stor andel af volumen ligger i top-varerne)

Kræver dato-kolonne for hastighed/interval. Mangler den, degraderes pænt
og motoren siger hvad den ikke kunne beregne. Leverandør-timing kræver
leverandør-kolonne — flagges som "ikke i data" hvis fraværende.

Gemini-laget (forklaring) ligger udenpå. Her regnes kun tal.
"""

from __future__ import annotations
import json
from collections import defaultdict
from statistics import mean
from salgsanalyse import load_lines, _round


def _date_span(lines):
    dates = [l["date"] for l in lines if l["date"]]
    if not dates:
        return None, None, None
    lo, hi = min(dates), max(dates)
    return lo, hi, (hi - lo).days + 1


def velocity(lines, span_days, top=15):
    qty = defaultdict(float)
    for l in lines:
        qty[l["product"]] += l["quantity"]
    out = []
    for p, q in qty.items():
        v = (q / span_days) if span_days else None
        out.append({"product": p, "units_sold": _round(q),
                    "units_per_day": _round(v, 3) if v is not None else None})
    out.sort(key=lambda x: (x["units_per_day"] or 0), reverse=True)
    return out[:top]


def repurchase_interval(lines, top=15, min_repeats=2):
    """Gns. dage mellem gange samme KUNDE køber samme produkt igen."""
    seq = defaultdict(list)  # (customer, product) -> [dates]
    for l in lines:
        if l["customer"] and l["date"]:
            seq[(l["customer"], l["product"])].append(l["date"])
    gaps_by_product = defaultdict(list)
    for (cust, prod), dates in seq.items():
        ds = sorted(dates)
        if len(ds) >= min_repeats:
            for a, b in zip(ds, ds[1:]):
                g = (b - a).days
                if g > 0:
                    gaps_by_product[prod].append(g)
    out = []
    for p, gaps in gaps_by_product.items():
        if gaps:
            out.append({"product": p,
                        "avg_days_between_repurchase": _round(mean(gaps), 1),
                        "observations": len(gaps)})
    out.sort(key=lambda x: x["avg_days_between_repurchase"])
    return out[:top]


def reorder_list(vel, intervals, top=10):
    """Genbestillingsliste: hurtigst-bevægende varer først. Hvis der findes
    et genkøbsinterval, foreslås en genbestillings-kadence ud fra det."""
    interval_map = {i["product"]: i["avg_days_between_repurchase"] for i in intervals}
    out = []
    for v in vel[:top]:
        p = v["product"]
        cadence = interval_map.get(p)
        out.append({
            "product": p,
            "units_per_day": v["units_per_day"],
            "suggested_reorder_cadence_days": cadence,
            "note": ("Hold på lager — hurtig omsætning."
                     + (f" Kunder genkøber ca. hver {cadence:.0f}. dag." if cadence else "")),
        })
    return out


def concentration(lines):
    qty = defaultdict(float)
    total = 0.0
    for l in lines:
        qty[l["product"]] += l["quantity"]
        total += l["quantity"]
    ranked = sorted(qty.values(), reverse=True)
    def share(n):
        return _round(sum(ranked[:n]) / total * 100, 1) if total else 0
    return {"total_units": _round(total), "distinct_products": len(qty),
            "top5_share_pct": share(5), "top10_share_pct": share(10)}


def analyze(csv_text: str) -> dict:
    lines, mapping = load_lines(csv_text)
    if not lines:
        return {"error": "Ingen brugbare salgslinjer fundet i CSV'en.", "column_mapping": mapping}
    lo, hi, span = _date_span(lines)
    warnings = []
    if not span:
        warnings.append("Ingen dato-kolonne fundet — salgshastighed og genkøbsinterval kan ikke beregnes.")
    if not any(l["customer"] for l in lines):
        warnings.append("Ingen kunde-kolonne fundet — genkøbsinterval kan ikke beregnes.")
    vel = velocity(lines, span) if span else []
    intervals = repurchase_interval(lines)
    return {
        "meta": {
            "column_mapping": mapping,
            "rows_used": len(lines),
            "date_from": lo, "date_to": hi, "span_days": span,
            "warnings": warnings,
        },
        "velocity": vel,
        "repurchase_intervals": intervals,
        "reorder_list": reorder_list(vel, intervals),
        "concentration": concentration(lines),
    }


if __name__ == "__main__":
    import sys
    print(json.dumps(analyze(open(sys.argv[1], encoding="utf-8").read()),
                     ensure_ascii=False, indent=2, default=str))
