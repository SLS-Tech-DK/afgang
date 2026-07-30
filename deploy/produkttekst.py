"""
SLS Tech · Afgang — Produkttekst-optimering (AEO)
-------------------------------------------------
Input: produktkatalog-CSV (produktnavn + beskrivelse [+ pris]).
Output pr. produkt: AEO-parathedsscore + hvad der skal forbedres.
Selve omskrivningen til bedre tekst = Gemini (interface). Her scores og
prissættes deterministisk.

Pris: 20 kr/produkt, min. 250 kr, batch-rabat >100 produkter (10%).
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
    return {"name": find(["produktnavn", "varenavn", "produkt", "vare", "title", "name", "navn"]),
            "desc": find(["beskrivelse", "description", "tekst", "body", "indhold", "content"]),
            "price": find(["pris", "price", "beloeb", "amount"])}


def score_description(text: str) -> dict:
    t = (text or "").strip()
    words = len(t.split())
    checks = {
        "laengde_ok": 20 <= words <= 200,                 # ikke for tynd, ikke roman
        "har_specifikationer": bool(re.search(r"\d", t)),  # tal = konkrethed (mål, vægt, antal)
        "har_spoergsmaal_svar": "?" in t,
        "ikke_kun_store_bogstaver": not (t.isupper() and len(t) > 10),
        "har_flere_saetninger": t.count(".") >= 2,
    }
    passed = sum(checks.values())
    return {"words": words, "checks": checks, "aeo_score": _round(passed / len(checks) * 100, 0)}


def price_quote(n_products: int) -> dict:
    base = n_products * 20
    total = max(base, 250)
    rabat = 0
    if n_products > 100:
        rabat = _round(total * 0.10)
        total = _round(total - rabat)
    return {"products": n_products, "pris_pr_produkt": 20, "minimum": 250,
            "batch_rabat": rabat, "total_ekskl_moms": _round(total)}


def analyze(csv_text: str) -> dict:
    try:
        delim = csv.Sniffer().sniff(csv_text[:2048], delimiters=",;\t|").delimiter
    except csv.Error:
        delim = ","
    reader = csv.DictReader(io.StringIO(csv_text), delimiter=delim)
    cols = _detect(reader.fieldnames or [])
    if not cols["name"] or not cols["desc"]:
        return {"error": "Katalog-CSV mangler produktnavn og/eller beskrivelse.",
                "columns_found": reader.fieldnames}
    rows = list(reader)
    scored = []
    for r in rows:
        name = (r.get(cols["name"]) or "").strip()
        if not name:
            continue
        s = score_description(r.get(cols["desc"]) or "")
        scored.append({"product": name, **s})
    if not scored:
        return {"error": "Ingen produkter fundet."}
    weak = [x for x in scored if x["aeo_score"] < 60]
    weak.sort(key=lambda x: x["aeo_score"])
    avg = _round(sum(x["aeo_score"] for x in scored) / len(scored), 0)
    return {
        "meta": {"columns": cols, "products": len(scored), "avg_aeo_score": avg},
        "weakest": weak[:20],
        "all_scores": scored,
        "pris": price_quote(len(scored)),
    }
