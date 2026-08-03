"""
SLS Tech · Afgang — AI-synlighed (GEO+AEO)
------------------------------------------
Input: kundens domæne/brand + konkurrenter + branche.
To dele:
  GEO (Generative Engine Optimization): bliver brandet nævnt når folk spørger
    AI-modeller om branchen? Score + share-of-voice vs. konkurrenter.
  AEO (Answer Engine Optimization): er kundens sider læsbare for AI-søgning?
    Audit af sidetekst for FAQ/spørgsmålsoverskrifter/struktur/kort-svar.

ÆRLIG ARKITEKTUR-GRÆNSE:
Selve AI-forespørgslerne (spørge modeller om branchen) sker via et injicerbart
querier-interface — mock i test, rigtig model (Gemini/Vertex) ved deployment.
  - Deterministisk score-/audit-kerne: testet.
  - Live model-forespørgsler: UTESTET indtil querier er wired.
"""

from __future__ import annotations
import re
from typing import Callable, Optional


def _round(x, n=1):
    return round(x + 0.0, n)


# --- GEO: synlighed i AI-svar -----------------------------------------------
def geo_visibility(query_results: list[dict], brand: str, competitors: list[str]) -> dict:
    """query_results: [{"query": str, "response": str}]. Tæller omtaler ved
    case-insensitiv delstrengs-match. Returnér mention-rate + share-of-voice."""
    brand_l = brand.lower()
    comp_l = [c.lower() for c in competitors]
    n = len(query_results)
    brand_hits = 0
    comp_hits = {c: 0 for c in competitors}
    per_query = []
    for qr in query_results:
        resp = (qr.get("response") or "").lower()
        b = brand_l in resp
        if b:
            brand_hits += 1
        cs = [competitors[i] for i, cl in enumerate(comp_l) if cl in resp]
        for c in cs:
            comp_hits[c] += 1
        per_query.append({"query": qr.get("query"), "brand_mentioned": b, "competitors_mentioned": cs})
    total_mentions = brand_hits + sum(comp_hits.values())
    sov = (brand_hits / total_mentions * 100) if total_mentions else 0
    return {
        "queries_run": n,
        "brand_mention_rate_pct": _round(brand_hits / n * 100) if n else 0,
        "share_of_voice_pct": _round(sov),
        "brand_mentions": brand_hits,
        "competitor_mentions": comp_hits,
        "per_query": per_query,
        "score": _round(min(100, brand_hits / n * 100 if n else 0)),
    }


def geo_quick_wins(vis: dict, brand: str) -> list[str]:
    wins = []
    if vis["brand_mention_rate_pct"] < 50:
        wins.append(f"{brand} nævnes i under halvdelen af AI-svarene — byg autoritetsindhold (FAQ, guides) som modellerne kan citere.")
    if vis["share_of_voice_pct"] < 33:
        wins.append("Din share-of-voice er lav vs. konkurrenterne — få omtaler/links fra sider AI-modeller ofte trækker på.")
    top_comp = max(vis["competitor_mentions"].items(), key=lambda x: x[1], default=(None, 0))
    if top_comp[0] and top_comp[1] > vis["brand_mentions"]:
        wins.append(f"'{top_comp[0]}' nævnes oftere end dig — analysér deres indhold og luk hullet.")
    if not wins:
        wins.append("Du står stærkt i AI-svar — hold indholdet opdateret og udbyg med flere spørgsmål/svar.")
    return wins[:5]


# --- AEO: er siderne læsbare for AI-søgning? --------------------------------
def aeo_audit(page_text: str) -> dict:
    """Deterministiske signaler for AI-læsbarhed i en sidetekst/HTML."""
    t = page_text or ""
    tl = t.lower()
    checks = {
        "har_spoergsmaalsoverskrifter": bool(re.search(r"(?m)^\s*#{1,6}?\s*.*\?\s*$", t)) or bool(re.search(r"<h[1-6][^>]*>[^<]*\?</h[1-6]>", tl)),
        "har_faq_struktur": ("faq" in tl) or ("ofte stillede" in tl) or ('"faqpage"' in tl) or ("faqpage" in tl),
        "har_schema_markup": ("application/ld+json" in tl) or ("schema.org" in tl),
        "har_korte_svar": _has_concise_answers(t),
        "har_lister": bool(re.search(r"(?m)^\s*[-*]\s+", t)) or ("<ul" in tl) or ("<ol" in tl),
    }
    passed = sum(1 for v in checks.values() if v)
    score = _round(passed / len(checks) * 100)
    anbefalinger = []
    if not checks["har_spoergsmaalsoverskrifter"]:
        anbefalinger.append("Tilføj overskrifter formuleret som spørgsmål (sådan søger folk i AI).")
    if not checks["har_faq_struktur"]:
        anbefalinger.append("Tilføj en FAQ-sektion med konkrete spørgsmål og svar.")
    if not checks["har_schema_markup"]:
        anbefalinger.append("Tilføj FAQPage/Product schema (JSON-LD) så AI kan læse strukturen.")
    if not checks["har_korte_svar"]:
        anbefalinger.append("Giv korte, direkte svar (1-3 sætninger) lige under hvert spørgsmål.")
    if not checks["har_lister"]:
        anbefalinger.append("Brug punktlister — de citeres lettere af AI.")
    return {"checks": checks, "score": score, "anbefalinger": anbefalinger[:5]}


def _has_concise_answers(t: str) -> bool:
    """Heuristik: findes der korte afsnit (<=300 tegn) lige efter en overskrift?"""
    blocks = re.split(r"\n\s*\n", t)
    return any(0 < len(b.strip()) <= 300 for b in blocks)


def analyze(query_results, brand, competitors, pages=None) -> dict:
    vis = geo_visibility(query_results or [], brand, competitors or [])
    result = {
        "meta": {"brand": brand, "competitors": competitors or [], "queries": len(query_results or [])},
        "geo": {**vis, "quick_wins": geo_quick_wins(vis, brand)},
    }
    if pages:
        audits = [{"page": p.get("name", f"side{i+1}"), **aeo_audit(p.get("text", ""))}
                  for i, p in enumerate(pages)]
        result["aeo"] = {"pages": audits,
                         "avg_score": _round(sum(a["score"] for a in audits) / len(audits)) if audits else 0}
    else:
        result["aeo"] = {"note": "Ingen sider givet — upload/angiv sider for AEO-audit (Pro)."}
    return result


# --- AI-query interface ------------------------------------------------------
def run_queries(prompts: list[str], querier: Optional[Callable[[str], str]] = None) -> list[dict]:
    """Kør et sæt branche-prompts mod en AI-model. `querier(prompt)->svar` wires
    til Gemini/Vertex ved deployment. UTESTET mod live model her."""
    if querier is None:
        raise NotImplementedError("Live querier ikke wired — injicér querier (Gemini/Vertex).")
    return [{"query": p, "response": querier(p)} for p in prompts]


# ============================================================================
# LIVE GEO — spørg rigtige AI-modeller (Gemini) om branchen
# ============================================================================
def default_gemini_querier():
    """Querier(prompt)->svar via Gemini flash (Vertex). Bruges i live GEO."""
    from gemini_forklaring import vertex_gemini_caller
    caller = vertex_gemini_caller()
    system = ("Du er en almindelig AI-assistent der svarer kort på danske forbrugerspørgsmål. "
              "Nævn konkrete brands/webshops når det er relevant, som du normalt ville.")
    return lambda prompt: caller(system, prompt)


def build_branche_prompts(field: str) -> list[str]:
    f = (field or "produktet").strip()
    return [
        f"Hvad er de bedste webshops til {f} i Danmark?",
        f"Hvor køber man {f} online?",
        f"Hvilken butik anbefaler du til {f}?",
        f"Bedste sted at købe {f}?",
        f"Hvem sælger {f} af god kvalitet?",
    ]


def analyze_live(brand: str, field: str, competitors=None, pages=None,
                 querier=None, caller=None) -> dict:
    """Fuld live GEO+AEO: generér branche-prompts → spørg Gemini → tæl omtaler.
    querier(prompt)->svar kan injiceres (mock i test)."""
    competitors = competitors or []
    q = querier or default_gemini_querier()
    prompts = build_branche_prompts(field)
    query_results = [{"query": p, "response": q(p)} for p in prompts]
    result = analyze(query_results, brand, competitors, pages)
    result["meta"]["field"] = field
    result["meta"]["live"] = True
    return result
