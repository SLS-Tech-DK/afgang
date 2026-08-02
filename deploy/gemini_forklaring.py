"""
SLS Tech · Afgang — Gemini-forklaringslag til Salgsanalyse
----------------------------------------------------------
Tager den DETERMINISTISKE analyse-JSON (fra salgsanalyse.analyze) og
producerer en kundevendt leverance på klar dansk: resumé + prioriterede
handlinger. Gemini forklarer KUN tallene den får — den må ikke opfinde tal.

Arkitektur (Sørens): motor bor i Google Cloud, LLM = Gemini via Vertex AI
(Google Workspace). Denne fil er model-agnostisk via en injiceret caller,
så den kan testes med en mock og køres live i produktion uden ændringer.

Test: mock-caller verificerer prompt-samling + output-kontrakt.
Live Vertex-kald: UTESTET indtil nøgle sidder på ved deployment.
"""

from __future__ import annotations
import json, os
from typing import Callable, Optional


SYSTEM_INSTRUKTION = (
    "Du er en nøgtern dansk e-handelsanalytiker for SLS Tech. "
    "Du får en FÆRDIG dataanalyse af en webshops egen salgsdata. "
    "Din opgave: forklar hvad tallene betyder og giv konkrete handlinger. "
    "REGLER: Brug KUN tal og fakta fra data nedenfor — opfind ALDRIG tal, "
    "produkter eller procenter der ikke står der. Skriv kort, konkret og på dansk. "
    "Ingen floskler. Kannibalisering er et SIGNAL, ikke bevis — formulér det som "
    "'undersøg om'. Afslut med en prioriteret handlingsliste (maks 5 punkter)."
)


def _byg_prompt(analysis: dict) -> str:
    """Samler bruger-prompten: kompakt, kun de felter Gemini skal ræsonnere på."""
    m = analysis.get("meta", {})
    dele = [
        f"BUTIKSNØGLETAL: {m.get('distinct_orders')} ordrer, "
        f"{m.get('distinct_products')} produkter, "
        f"total omsætning {m.get('total_revenue')} kr, "
        f"gns. ordreværdi {m.get('avg_order_value')} kr.",
        "",
        "BESTSELLERE (efter omsætning):",
        json.dumps(analysis.get("bestsellers", {}).get("by_revenue", []), ensure_ascii=False),
        "",
        "SVAGEST SÆLGENDE:",
        json.dumps(analysis.get("bestsellers", {}).get("worst_by_revenue", []), ensure_ascii=False),
        "",
        "KØBES-SAMMEN (par + hvor mange gange + lift):",
        json.dumps(analysis.get("co_purchase", []), ensure_ascii=False),
        "",
        "BUNDLE-KANDIDATER:",
        json.dumps(analysis.get("bundles", []), ensure_ascii=False),
        "",
        "KANNIBALISERINGS-SIGNALER (undersøg — ikke bevis):",
        json.dumps(analysis.get("cannibalization", []), ensure_ascii=False),
        "",
        "Skriv leverancen: 1) kort resumé (3-5 linjer), 2) hvad der driver "
        "omsætningen, 3) bundle-muligheder, 4) mulige kannibaliseringer at "
        "undersøge, 5) prioriteret handlingsliste (maks 5).",
    ]
    return "\n".join(dele)


# --- Model-callere -----------------------------------------------------------
# En caller er: (system_instruktion: str, prompt: str) -> str

def vertex_gemini_caller(model: Optional[str] = None) -> Callable[[str, str], str]:
    """Live Vertex AI-caller. Kræver at google-cloud-aiplatform er installeret
    og at miljøet er autentificeret (GOOGLE_CLOUD_PROJECT + ADC / service-konto).
    UTESTET mod live API i denne session — verificér ved deployment."""
    def _call(system: str, prompt: str) -> str:
        mdl = model or os.environ.get("GEMINI_MODEL", "gemini-2.0-flash")
        import vertexai
        from vertexai.generative_models import GenerativeModel
        project = os.environ.get("GOOGLE_CLOUD_PROJECT")
        location = os.environ.get("VERTEX_LOCATION", "europe-north1")
        vertexai.init(project=project, location=location)
        gm = GenerativeModel(mdl, system_instruction=system)
        resp = gm.generate_content(prompt, generation_config={"temperature": 0.2})
        return resp.text
    return _call


def forklar(analysis: dict, caller: Optional[Callable[[str, str], str]] = None) -> dict:
    """Producér den kundevendte forklaring. Injicér `caller` (mock i test,
    vertex_gemini_caller() i produktion). Returnér struktureret resultat."""
    if analysis.get("error"):
        return {"error": analysis["error"]}
    if caller is None:
        caller = vertex_gemini_caller()
    prompt = _byg_prompt(analysis)
    tekst = caller(SYSTEM_INSTRUKTION, prompt)
    return {
        "forklaring_tekst": tekst,
        "prompt_brugt": prompt,          # gemmes til revision/debug
        "model": "gemini (vertex)",
        "note": "Tekst er LLM-genereret ud fra de deterministiske tal. Tal selv er beregnet, ikke gættet.",
    }


if __name__ == "__main__":
    import sys
    from salgsanalyse import analyze
    data = analyze(open(sys.argv[1], encoding="utf-8").read())
    print(json.dumps(forklar(data, caller=lambda s, p: "[mock]"), ensure_ascii=False, indent=2))
