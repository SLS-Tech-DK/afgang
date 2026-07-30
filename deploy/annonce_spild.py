"""
SLS Tech · Afgang — Annonce-spildsanalyse
-----------------------------------------
Input: annonce-CSV (kampagne/annoncegruppe, forbrug, klik, konverteringer,
omsætning). Output: ROAS, CPA, CTR, konverteringsrate pr. kampagne, og en
prioriteret spildliste (højt forbrug, lav/ingen afkast).
Deterministisk. Nuanceret vurdering = Gemini (interface).
"""
from __future__ import annotations
import re, csv, io
from salgsanalyse import _to_float


def _round(x, n=2):
    return round(x + 0.0, n)


def _detect(headers):
    def find(cands):
        for h in headers:
            hl = re.sub(r"[^a-z0-9]", "", h.lower())
            if any(re.sub(r"[^a-z0-9]", "", c) in hl for c in cands):
                return h
        return None
    return {"campaign": find(["kampagne", "campaign", "annoncegruppe", "adgroup", "ad ", "annonce", "navn", "name"]),
            "spend": find(["forbrug", "spend", "cost", "omkostning", "brugt"]),
            "clicks": find(["klik", "clicks", "click"]),
            "conversions": find(["konvertering", "conversion", "salg", "orders", "ordrer", "conv"]),
            "revenue": find(["omsætning", "omsaetning", "revenue", "værdi", "vaerdi", "value", "sales"])}


def analyze(csv_text: str, min_spend_flag: float = 100.0) -> dict:
    try:
        delim = csv.Sniffer().sniff(csv_text[:2048], delimiters=",;\t|").delimiter
    except csv.Error:
        delim = ","
    reader = csv.DictReader(io.StringIO(csv_text), delimiter=delim)
    cols = _detect(reader.fieldnames or [])
    if not cols["campaign"] or not cols["spend"]:
        return {"error": "Annonce-CSV mangler kampagne og/eller forbrug.",
                "columns_found": reader.fieldnames}
    rows = []
    tot_spend = tot_rev = 0.0
    for r in reader:
        name = (r.get(cols["campaign"]) or "").strip()
        if not name:
            continue
        spend = _to_float(r.get(cols["spend"])) or 0
        clicks = _to_float(r.get(cols["clicks"])) if cols["clicks"] else None
        conv = _to_float(r.get(cols["conversions"])) if cols["conversions"] else None
        rev = _to_float(r.get(cols["revenue"])) if cols["revenue"] else None
        roas = _round(rev / spend, 2) if (rev is not None and spend) else None
        cpa = _round(spend / conv, 2) if (conv) else None
        conv_rate = _round(conv / clicks * 100, 2) if (conv is not None and clicks) else None
        rows.append({"campaign": name, "spend": _round(spend), "clicks": clicks,
                     "conversions": conv, "revenue": _round(rev) if rev is not None else None,
                     "roas": roas, "cpa": cpa, "conversion_rate_pct": conv_rate})
        tot_spend += spend
        if rev:
            tot_rev += rev
    # spild: højt forbrug og (ingen konverteringer, eller ROAS < 1)
    waste = []
    for r in rows:
        if r["spend"] >= min_spend_flag and (
            (r["conversions"] is not None and r["conversions"] == 0) or
            (r["roas"] is not None and r["roas"] < 1)):
            reason = "ingen konverteringer" if (r["conversions"] == 0) else f"ROAS {r['roas']} (tab)"
            waste.append({**r, "reason": reason})
    waste.sort(key=lambda x: x["spend"], reverse=True)
    total_waste = _round(sum(w["spend"] for w in waste))
    return {
        "meta": {"columns": cols, "campaigns": len(rows),
                 "total_spend": _round(tot_spend), "total_revenue": _round(tot_rev),
                 "overall_roas": _round(tot_rev / tot_spend, 2) if tot_spend else None,
                 "min_spend_flag": min_spend_flag},
        "per_campaign": rows,
        "waste": waste,
        "estimated_wasted_spend": total_waste,
    }
