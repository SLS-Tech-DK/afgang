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
from paths import resolve_type
import base64, webshop_suite

# Motorer (deterministisk analyze) + valgfrit forklar-lag pr. type.
import salgsanalyse, indkobsanalyse, lageranalyse, kundeanalyse, butiksanalyse
import konkurrentanalyse, ai_synlighed, prisovervagning, naevner_ai_alarm
import produkttekst, review_analyse, landingsside, annonce_spild, soegeords_gap
import gemini_forklaring, indkob_forklaring, lager_forklaring, kunde_forklaring
import konk_forklaring, ai_forklaring, butiks_forklaring, review_forklaring


def _csv(body):     # motorer der tager rå CSV-tekst
    return body.get("csv", "")




def _suite(product, b):
    if b.get("demo"):
        out = {"demo": True, "produkt": product}
        try: out["html"] = webshop_suite.demo(product, "html")
        except Exception as e: out["html_error"] = str(e)
        try: out["xlsx_base64"] = base64.b64encode(webshop_suite.demo(product, "xlsx")).decode()
        except Exception as e: out["xlsx_error"] = str(e)
        return out
    a = webshop_suite.analyze(b.get("vare_csv", ""), b.get("ordre_csv", ""))
    if a.get("error"): return a
    out = {"meta": a["meta"], "analyse": a}
    try: out["html"] = webshop_suite.render_html(a, b.get("shop_name", ""), product=product)
    except Exception as e: out["html_error"] = str(e)
    try: out["xlsx_base64"] = base64.b64encode(webshop_suite.render_xlsx(a, product=product)).decode()
    except Exception as e: out["xlsx_error"] = str(e)
    return out


def _konk(b):
    dom = b.get("domain") or b.get("own_domain")
    if dom:
        r = konkurrentanalyse.analyze_web(dom, b.get("competitor_domains") or [c for c in b.get("competitors", []) if isinstance(c, str)])
    else:
        r = konkurrentanalyse.analyze(b.get("own", {}), b.get("competitors", []))
    if not r.get("error"):
        try: r["html"] = webshop_suite.render_konkurrent_html(r, b.get("shop_name", ""))
        except Exception as e: r["html_error"] = str(e)
    return r

def _ai(b):
    if b.get("brand") and not b.get("query_results"):
        r = ai_synlighed.analyze_live(b.get("brand", ""), b.get("field", ""), b.get("competitors", []), b.get("pages"))
    else:
        r = ai_synlighed.analyze(b.get("query_results", []), b.get("brand", ""), b.get("competitors", []), b.get("pages"))
    if not r.get("error"):
        try: r["html"] = webshop_suite.render_ai_html(r, b.get("shop_name", ""))
        except Exception as e: r["html_error"] = str(e)
    return r


REGISTRY = {
    # type: (analyze(body) -> dict, forklar-modul eller None)
    "salgsanalyse":     (lambda b: _suite("salgsanalyse", b), None),
    "indkobsanalyse":   (lambda b: _suite("indkobsanalyse", b), None),
    "lageranalyse":     (lambda b: _suite("lageranalyse", b), None),
    "kundeanalyse":     (lambda b: _suite("kundeanalyse", b), None),
    "butiksanalyse":    (lambda b: _suite("fuld_butiksanalyse", b), None),
    "konkurrentanalyse": (lambda b: _konk(b), None),
    "ai_synlighed":     (lambda b: _ai(b), ai_forklaring),
    "prisovervagning":  (lambda b: prisovervagning.analyze(b.get("current", []), b.get("previous"), b.get("threshold_pct", 1.0)), None),
    "naevner_ai_alarm": (lambda b: naevner_ai_alarm.run_check(b.get("query_results", []), b.get("brand", ""), b.get("competitors", []), b.get("previous_measurement")), None),
    "produkttekst":     (lambda b: produkttekst.analyze(_csv(b)), None),
    "review_analyse":   (lambda b: review_analyse.analyze(_csv(b)), review_forklaring),
    "landingsside":     (lambda b: landingsside.analyze(b.get("page_text", ""), b.get("page_name", "landingsside")), None),
    "annonce_spild":    (lambda b: annonce_spild.analyze(_csv(b)), None),
    "fuld_butiksanalyse": (lambda b: _suite("fuld_butiksanalyse", b), None),
    "spoerg_data":        (lambda b: webshop_suite.gemini_qa(b.get("analyse", {}), b.get("spoergsmaal", "")), None),
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
def _json(payload, code):
    return (json.dumps(payload, ensure_ascii=False, default=str), code,
            {"Content-Type": "application/json; charset=utf-8"})


def handler(request):
    path = getattr(request, "path", "") or "/"
    if request.method == "GET":
        seg = path.strip("/").split("/", 1)[0]
        if seg in ("", "health", "healthz"):
            return _json({"ok": True, "service": "afgang-motorer", "products": sorted(REGISTRY)}, 200)
        t = resolve_type({}, path)
        if t in REGISTRY:
            return _json({"ok": True, "type": t, "hint": "POST JSON hertil for at k\u00f8re analysen."}, 200)
        return _json({"ok": False, "error": f"Ukendt sti '{path}'. Gyldige produkter: {sorted(REGISTRY)}"}, 404)
    if request.method != "POST":
        return _json({"ok": False, "error": "Brug POST med JSON"}, 405)
    try:
        body = request.get_json(silent=True) or {}
    except Exception:
        body = {}
    t = resolve_type(body, path)
    if t and not body.get("type"):
        body = {**body, "type": t}
    resp = route(body)
    code = 200 if resp.get("ok") else 400
    return _json(resp, code)
