"""Gemini-forklaringslag til Konkurrentanalyse. Samme caller-mønster.
Live Vertex-kald: UTESTET indtil nøgle ved deployment."""
from __future__ import annotations
import json
from typing import Callable, Optional
from gemini_forklaring import vertex_gemini_caller

SYSTEM_INSTRUKTION = (
    "Du er en nøgtern dansk konkurrentanalytiker for SLS Tech. Du får en FÆRDIG "
    "sammenligning mellem en webshop og dens konkurrenter. Forklar hvor kunden "
    "står stærkt, hvor de er bagud, og hvor de konkret kan vinde. REGLER: brug "
    "KUN tallene nedenfor, opfind aldrig tal. Kort, konkret, dansk. Afslut med "
    "en prioriteret handlingsliste (maks 5)."
)


def _byg_prompt(a: dict) -> str:
    m = a.get("meta", {})
    dele = [
        f"SAMMENLIGNING: {m.get('own')} vs. {', '.join(m.get('competitors') or []) or 'ingen'}.",
        "SIDE-OM-SIDE:", json.dumps(a.get("side_by_side", {}), ensure_ascii=False, default=str),
        "GAPS (foran/bagud pr. felt):", json.dumps(a.get("gaps", []), ensure_ascii=False, default=str),
        "HVOR DU KAN VINDE:", json.dumps(a.get("where_to_win", []), ensure_ascii=False, default=str),
        "Skriv: 1) resumé af hvor kunden står, 2) styrker, 3) svagheder, 4) prioriteret handlingsliste (maks 5).",
    ]
    return "\n".join(d for d in dele if d)


def forklar(analysis: dict, caller: Optional[Callable[[str, str], str]] = None) -> dict:
    if analysis.get("error"):
        return {"error": analysis["error"]}
    if caller is None:
        caller = vertex_gemini_caller()
    prompt = _byg_prompt(analysis)
    return {"forklaring_tekst": caller(SYSTEM_INSTRUKTION, prompt), "prompt_brugt": prompt,
            "model": "gemini (vertex)", "note": "LLM-tekst ud fra deterministiske sammenligningstal."}
