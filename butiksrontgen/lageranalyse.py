"""
SLS Tech · Afgang — Lageranalyse-motor (delelement af Butiksrøntgen)
-------------------------------------------------------------------
Deterministisk. Genbruger CSV-genkendelseslaget fra salgsanalyse.
Fra REN salgsdata beregnes:
  - dødvarer (ingen salg i de seneste N dage)
  - langsomtsælgende (lav hastighed)
  - sæsonmønster (salg pr. måned)

Ærlig grænse: ægte KAPITALBINDING kræver lagerbeholdning + kostpris, som
ikke findes i en ordre-CSV. Kan kunden uploade en lager-CSV (SKU, antal på
lager, kostpris), beregnes kapitalbinding også — ellers flagges det som
"kræver lager-data" i stedet for at blive gættet.
"""

from __future__ import annotations
import json
from collections import defaultdict
from datetime import timedelta
from salgsanalyse import load_lines, _to_float, _round
import csv, io


def deadstock(lines, ref_date, days=90):
    last_sale = {}
    for l in lines:
        if l["date"]:
            p = l["product"]
            if p not in last_sale or l["date"] > last_sale[p]:
                last_sale[p] = l["date"]
    cutoff = ref_date - timedelta(days=days)
    dead = [{"product": p, "last_sold": d, "days_since": (ref_date - d).days}
            for p, d in last_sale.items() if d < cutoff]
    dead.sort(key=lambda x: x["days_since"], reverse=True)
    return dead


def slow_movers(lines, span_days, top=15):
    qty = defaultdict(float)
    for l in lines:
        qty[l["product"]] += l["quantity"]
    out = [{"product": p, "units_sold": _round(q),
            "units_per_day": _round(q / span_days, 3) if span_days else None}
           for p, q in qty.items()]
    out.sort(key=lambda x: (x["units_per_day"] or 0))
    return out[:top]


def seasonality(lines):
    by_month = defaultdict(float)
    for l in lines:
        if l["date"]:
            by_month[f"{l['date'].year}-{l['date'].month:02d}"] += l["revenue"]
    return [{"month": m, "revenue": _round(v)} for m, v in sorted(by_month.items())]


def capital_tied(stock_csv_text):
    """Valgfri: lager-CSV med produkt, antal-på-lager, kostpris → kapitalbinding."""
    try:
        dialect = csv.Sniffer().sniff(stock_csv_text[:2048], delimiters=",;\t|")
        delim = dialect.delimiter
    except csv.Error:
        delim = ","
    reader = csv.DictReader(io.StringIO(stock_csv_text), delimiter=delim)
    headers = reader.fieldnames or []
    def find(cands):
        for h in headers:
            hl = h.lower()
            if any(c in hl for c in cands):
                return h
        return None
    h_prod = find(["produkt", "vare", "product", "item", "sku", "navn", "name"])
    h_stock = find(["lager", "beholdning", "stock", "qty", "antal", "quantity", "on hand"])
    h_cost = find(["kostpris", "cost", "indkøbspris", "kost", "buy price"])
    if not (h_prod and h_stock and h_cost):
        return {"error": "Lager-CSV mangler en af: produkt, lagerantal, kostpris.",
                "headers_found": headers}
    rows = []
    total = 0.0
    for r in reader:
        stock = _to_float(r.get(h_stock)) or 0
        cost = _to_float(r.get(h_cost)) or 0
        tied = stock * cost
        total += tied
        rows.append({"product": (r.get(h_prod) or "").strip(),
                     "stock": _round(stock), "unit_cost": _round(cost),
                     "capital_tied": _round(tied)})
    rows.sort(key=lambda x: x["capital_tied"], reverse=True)
    return {"total_capital_tied": _round(total), "by_product": rows[:20]}


def analyze(csv_text: str, stock_csv_text: str | None = None, deadstock_days: int = 90) -> dict:
    lines, mapping = load_lines(csv_text)
    if not lines:
        return {"error": "Ingen brugbare salgslinjer fundet.", "column_mapping": mapping}
    dates = [l["date"] for l in lines if l["date"]]
    warnings = []
    ref = max(dates) if dates else None
    span = (max(dates) - min(dates)).days + 1 if dates else None
    if not dates:
        warnings.append("Ingen dato-kolonne — dødvare og sæson kan ikke beregnes.")
    result = {
        "meta": {"column_mapping": mapping, "rows_used": len(lines),
                 "reference_date": ref, "span_days": span, "warnings": warnings},
        "deadstock": deadstock(lines, ref, deadstock_days) if ref else [],
        "slow_movers": slow_movers(lines, span),
        "seasonality": seasonality(lines),
    }
    if stock_csv_text:
        result["capital_tied"] = capital_tied(stock_csv_text)
    else:
        result["capital_tied"] = {"note": "Upload en lager-CSV (produkt, lagerantal, kostpris) for at beregne kapitalbinding. Kan ikke udledes af ordredata alene."}
    return result


if __name__ == "__main__":
    import sys
    print(json.dumps(analyze(open(sys.argv[1], encoding="utf-8").read()),
                     ensure_ascii=False, indent=2, default=str))
