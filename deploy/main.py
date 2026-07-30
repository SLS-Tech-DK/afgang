"""
SLS Tech · Afgang — Cloud Function-router (functions-framework, gen2)
--------------------------------------------------------------------
Én HTTP-funktion der ruter til den rigtige motor ud fra "type". Deployes til
Cloud Run/Functions i europe-north1. Bevidst valg: én routet funktion frem for
14 separate — samme kodebase, ét deploy, nemmere at vedligeholde. Hver type har
sin egen klare handler i REGISTRY.

Input (POST JSON): {"type": "salgsanalyse", "csv": "...", ...}
Output: {"ok": true, "type": ..., "result": {...}}  (deterministisk analyse)
Gemini-forklaring tilføjes hvis GEMINI_ENABLED=1 og motoren har et forklar-lag.

Deterministisk routing testet lokalt (test_router.py). Live Vertex/scraping/
AI-query wires ved deploy — se README-deploy.md.
"""
from __future__ import annotations
import os, json

# Motorer (deterministisk analyze) + valgfrit forklar-lag pr. type.
import salgsanalyse, indkobsanalyse, lageranalyse, kundeanalyse, butiksanalyse
import konkurrentanalyse, ai_synlighed, prisovervagning, naevner_ai_alarm
import produkttekst, review_analyse, landingsside, annonce_spild, soegeords_gap
import gemini_forklaring, indkob_forklaring, lager_forklaring, kunde_forklaring
import konk_forklaring, ai_forklaring


def _csv(body):     # motorer der tager rå CSV-tekst
    return body.get("csv", "")


REGISTRY = {
    # type: (analyze(body) -> dict, forklar-modul eller None)
    "salgsanalyse":     (lambda b: salgsanalyse.analyze(_csv(b)), gemini_forklaring),
    "indkobsanalyse":   (lambda b: indkobsanalyse.analyze(_csv(b)), indkob_forklaring),
    "lageranalyse":     (lambda b: lageranalyse.analyze(_csv(b), b.get("stock_csv")), lager_forklaring),
    "kundeanalyse":     (lambda b: kundeanalyse.analyze(_csv(b)), kunde_forklaring),
    "butiksanalyse":    (lambda b: butiksanalyse.analyze(_csv(b), b.get("stock_csv")), None),
    "konkurrentanalyse":(lambda b: konkurrentanalyse.analyze(b.get("own", {}), b.get("competitors", [])), konk_forklaring),
    "ai_synlighed":     (lambda b: ai_synlighed.analyze(b.get("query_results", []), b.get("brand", ""), b.get("competitors", []), b.get("pages")), ai_forklaring),
    "prisovervagning":  (lambda b: prisovervagning.analyze(b.get("current", []), b.get("previous"), b.get("threshold_pct", 1.0)), None),
    "naevner_ai_alarm": (lambda b: naevner_ai_alarm.run_check(b.get("query_results", []), b.get("brand", ""), b.get("competitors", []), b.get("previous_measurement")), None),
    "produkttekst":     (lambda b: produkttekst.analyze(_csv(b)), None),
    "review_analyse":   (lambda b: review_analyse.analyze(_csv(b)), None),
    "landingsside":     (lambda b: landingsside.analyze(b.get("page_text", ""), b.get("page_name", "landingsside")), None),
    "annonce_spild":    (lambda b: annonce_spild.analyze(_csv(b)), None),
    "soegeords_gap":    (lambda b: soegeords_gap.analyze(_csv(b)), None),
}


def route(body: dict) -> dict:
    """Ren funktion — testbar uden HTTP. Ruter body til rette motor."""
    t = (body or {}).get("type")
    if t not in REGISTRY:
        return {"ok": False, "error": f"Ukendt type '{t}'. Gyldige: {sorted(REGISTRY)}"}
    analyze_fn, forklar_mod = REGISTRY[t]
    result = analyze_fn(body)
    out = {"ok": not result.get("error"), "type": t, "result": result}
    if os.environ.get("GEMINI_ENABLED") == "1" and forklar_mod and not result.get("error"):
        try:
            out["forklaring"] = forklar_mod.forklar(result)   # bruger live Vertex-caller
        except Exception as e:                                  # noqa
            out["forklaring_error"] = str(e)
    return out


# --- functions-framework entrypoint (HTTP) ----------------------------------
def handler(request):
    """Cloud Function/Run HTTP-entry. functions-framework kalder denne."""
    if request.method != "POST":
        return (json.dumps({"ok": False, "error": "Brug POST med JSON"}), 405,
                {"Content-Type": "application/json"})
    try:
        body = request.get_json(silent=True) or {}
    except Exception:
        body = {}
    resp = route(body)
    code = 200 if resp.get("ok") else 400
    return (json.dumps(resp, ensure_ascii=False, default=str), code,
            {"Content-Type": "application/json; charset=utf-8"})
