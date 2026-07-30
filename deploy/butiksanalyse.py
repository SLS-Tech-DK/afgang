"""
SLS Tech · Afgang — Fuld Butiksanalyse (premium "Butiksrøntgen")
---------------------------------------------------------------
Samle-motor. Kører alle fire delanalyser på samme upload og tilføjer
KRYDSANALYSER der ikke fås ved at købe delene hver for sig:
  - margin på tværs (kræver lager-CSV med kostpris — ellers flagget)
  - kannibalisering på tværs (fra salgsanalyse)
  - samlet, prioriteret 1-sides handlingsplan (deterministisk sammenvejning)

Deterministisk kerne. Gemini-forklaringslag ligger udenpå (forklar_fuld).
"""

from __future__ import annotations
import json
from collections import defaultdict
import salgsanalyse, indkobsanalyse, lageranalyse, kundeanalyse
from salgsanalyse import load_lines, _round


def _margin_paa_tvaers(csv_text, stock_csv_text):
    """Omsætning pr. produkt (fra salg) × kostpris (fra lager-CSV) → bruttomargin."""
    if not stock_csv_text:
        return {"note": "Upload lager-CSV med kostpris for at beregne margin på tværs."}
    cap = lageranalyse.capital_tied(stock_csv_text)
    if "error" in cap:
        return {"note": cap["error"]}
    cost_by_prod = {r["product"].lower(): r["unit_cost"] for r in cap["by_product"]}
    lines, _ = load_lines(csv_text)
    rev = defaultdict(float); qty = defaultdict(float)
    for l in lines:
        rev[l["product"]] += l["revenue"]; qty[l["product"]] += l["quantity"]
    out = []
    for p in rev:
        cost = cost_by_prod.get(p.lower())
        if cost is None:
            continue
        cogs = cost * qty[p]
        margin = rev[p] - cogs
        pct = (margin / rev[p] * 100) if rev[p] else 0
        out.append({"product": p, "revenue": _round(rev[p]), "cogs": _round(cogs),
                    "gross_margin": _round(margin), "margin_pct": _round(pct, 1)})
    out.sort(key=lambda x: x["gross_margin"], reverse=True)
    return {"by_product": out[:20]} if out else {"note": "Ingen produkter matchede mellem salg og lager-CSV."}


def _handlingsplan(salg, indkob, lager, kunde):
    """Sammenvejer de vigtigste fund til én prioriteret liste (deterministisk)."""
    plan = []
    bs = salg.get("bestsellers", {}).get("by_revenue", [])
    if bs:
        plan.append(f"Beskyt din topseller '{bs[0]['product']}' ({bs[0]['revenue']} kr) — sørg for den aldrig er udsolgt.")
    bundles = salg.get("bundles", [])
    if bundles:
        b = bundles[0]["products"]
        plan.append(f"Lav en bundle af {b[0]} + {b[1]} — de købes allerede sammen.")
    dead = lager.get("deadstock", [])
    if dead:
        plan.append(f"Ryd ud i dødvarer: '{dead[0]['product']}' (intet salg i {dead[0]['days_since']} dage).")
    reorder = indkob.get("reorder_list", [])
    if reorder:
        plan.append(f"Genbestil hurtigt-bevægende varer, start med '{reorder[0]['product']}'.")
    churn = kunde.get("churn_signal", []) if isinstance(kunde, dict) else []
    if churn:
        plan.append(f"Vind churn-kunder tilbage — {len(churn)} kunder har ikke købt længe.")
    cann = salg.get("cannibalization", [])
    if cann:
        c = cann[0]["products"]
        plan.append(f"Undersøg mulig kannibalisering: {c[0]} vs. {c[1]}.")
    return plan[:5]


def analyze(csv_text: str, stock_csv_text: str | None = None) -> dict:
    salg = salgsanalyse.analyze(csv_text)
    if salg.get("error"):
        return {"error": salg["error"]}
    indkob = indkobsanalyse.analyze(csv_text)
    lager = lageranalyse.analyze(csv_text, stock_csv_text=stock_csv_text)
    kunde = kundeanalyse.analyze(csv_text)   # kan give error hvis ingen kunde-kolonne
    return {
        "meta": salg.get("meta", {}),
        "salgsanalyse": salg,
        "indkobsanalyse": indkob,
        "lageranalyse": lager,
        "kundeanalyse": kunde,
        "kryds": {
            "margin_paa_tvaers": _margin_paa_tvaers(csv_text, stock_csv_text),
            "kannibalisering": salg.get("cannibalization", []),
        },
        "handlingsplan": _handlingsplan(salg, indkob, lager, kunde),
    }


if __name__ == "__main__":
    import sys
    print(json.dumps(analyze(open(sys.argv[1], encoding="utf-8").read()),
                     ensure_ascii=False, indent=2, default=str))
