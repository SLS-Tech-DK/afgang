"""Gemini-forklaringslag til AI-synlighed (GEO+AEO). Samme caller-mønster.
Live Vertex-kald: UTESTET indtil nøgle ved deployment."""
from __future__ import annotations
import json
from typing import Callable, Optional
from gemini_forklaring import vertex_gemini_caller

SYSTEM_INSTRUKTION = (
    "Du er en nøgtern dansk AI-synligheds-rådgiver (GEO/AEO) for SLS Tech. Du får "
    "en FÆRDIG analyse af om et brand nævnes i AI-svar og hvor læsbare deres sider "
    "er for AI-søgning. REGLER: brug KUN tallene nedenfor, opfind aldrig tal. Kort, "
    "konkret, dansk. Afslut med en prioriteret handlingsliste (maks 5)."
)


def _byg_prompt(a: dict) -> str:
    m = a.get("meta", {})
    dele = [
        f"BRAND: {m.get('brand')} vs. {', '.join(m.get('competitors') or []) or 'ingen'}. {m.get('queries')} AI-forespørgsler kørt.",
        "GEO (synlighed i AI-svar):", json.dumps(a.get("geo", {}), ensure_ascii=False, default=str),
        "AEO (sidernes AI-læsbarhed):", json.dumps(a.get("aeo", {}), ensure_ascii=False, default=str),
        "Skriv: 1) resumé (nævnes de eller ej), 2) GEO — synlighed vs. konkurrenter, 3) AEO — hvad skal sider rettes, 4) prioriteret handlingsliste (maks 5).",
    ]
    return "\n".join(d for d in dele if d)


def forklar(analysis: dict, caller: Optional[Callable[[str, str], str]] = None) -> dict:
    if analysis.get("error"):
        return {"error": analysis["error"]}
    if caller is None:
        caller = vertex_gemini_caller()
    prompt = _byg_prompt(analysis)
    return {"forklaring_tekst": caller(SYSTEM_INSTRUKTION, prompt), "prompt_brugt": prompt,
            "model": "gemini (vertex)", "note": "LLM-tekst ud fra deterministiske synligheds-/audit-tal."}
