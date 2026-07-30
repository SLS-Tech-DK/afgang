"""Gemini-forklaringslag til Indkøbsanalyse. Genbruger caller-infrastrukturen
fra gemini_forklaring (Vertex/mock). Oversætter indkøbs-tallene til kundevendt
dansk: hvad skal bestilles hjem, hvornår, og hvad man skal passe på.
Live Vertex-kald: UTESTET indtil nøgle ved deployment."""

from __future__ import annotations
import json
from typing import Callable, Optional
from gemini_forklaring import vertex_gemini_caller

SYSTEM_INSTRUKTION = (
    "Du er en nøgtern dansk indkøbs-/lagerrådgiver for SLS Tech. Du får en "
    "FÆRDIG analyse af en webshops egen salgshistorik. Forklar hvad der skal "
    "bestilles hjem, hvor tit, og hvad der er risiko for udsolgt. REGLER: brug "
    "KUN tallene nedenfor, opfind aldrig tal. Kort, konkret, dansk. Afslut med "
    "en prioriteret genbestillingsliste (maks 5)."
)


def _byg_prompt(a: dict) -> str:
    m = a.get("meta", {})
    dele = [
        f"PERIODE: {m.get('date_from')} til {m.get('date_to')} ({m.get('span_days')} dage). "
        f"{m.get('rows_used')} salgslinjer.",
        ("ADVARSLER: " + "; ".join(m.get("warnings", []))) if m.get("warnings") else "",
        "",
        "SALGSHASTIGHED (enheder/dag, hurtigst først):",
        json.dumps(a.get("velocity", []), ensure_ascii=False),
        "",
        "GENKØBSINTERVAL (gns. dage før samme kunde køber igen):",
        json.dumps(a.get("repurchase_intervals", []), ensure_ascii=False),
        "",
        "GENBESTILLINGSLISTE (rådata):",
        json.dumps(a.get("reorder_list", []), ensure_ascii=False),
        "",
        "KONCENTRATION:",
        json.dumps(a.get("concentration", {}), ensure_ascii=False),
        "",
        "Skriv: 1) kort resumé, 2) hvad der skal bestilles hjem og hvorfor, "
        "3) varer med risiko for hurtig udsolgt, 4) prioriteret genbestillingsliste (maks 5).",
    ]
    return "\n".join(d for d in dele if d != "")


def forklar(analysis: dict, caller: Optional[Callable[[str, str], str]] = None) -> dict:
    if analysis.get("error"):
        return {"error": analysis["error"]}
    if caller is None:
        caller = vertex_gemini_caller()
    prompt = _byg_prompt(analysis)
    tekst = caller(SYSTEM_INSTRUKTION, prompt)
    return {"forklaring_tekst": tekst, "prompt_brugt": prompt, "model": "gemini (vertex)",
            "note": "LLM-tekst ud fra deterministiske tal. Tal er beregnet, ikke gættet."}
