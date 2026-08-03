"""Gemini-forklaringslag til Review-analyse. Tager de deterministiske tal +
tema-optælling og skriver en nuanceret dansk sammenfatning + prioriteret plan.
Samme caller-mønster som resten. Live Vertex UTESTET indtil deploy."""
from __future__ import annotations
import json
from typing import Callable, Optional
from gemini_forklaring import vertex_gemini_caller

SYSTEM = ("Du er en nøgtern dansk e-handelsrådgiver. Du får en FÆRDIG analyse af en "
          "webshops kundeanmeldelser (ratingfordeling + temaer). Forklar hvad der driver "
          "de dårlige anmeldelser, og hvad der koster salg. Brug KUN tallene nedenfor, "
          "opfind intet. Kort, dansk, konkret. Afslut med prioriteret handlingsliste (maks 5).")


def _byg(a: dict) -> str:
    m = a.get("meta", {})
    return "\n".join([
        f"ANMELDELSER: {m.get('reviews')} stk, gns. rating {m.get('avg_rating')}, "
        f"andel dårlige (<= {m.get('low_threshold')}): {m.get('low_rating_share_pct')}%.",
        f"RATINGFORDELING: {json.dumps(a.get('rating_distribution', {}), ensure_ascii=False)}",
        f"TEMAER (alle): {json.dumps(a.get('themes', []), ensure_ascii=False)}",
        f"TEMAER I DÅRLIGE ANMELDELSER: {json.dumps(a.get('themes_in_low_reviews', []), ensure_ascii=False)}",
        "Skriv: 1) kort resumé, 2) hvad går galt (temaer i dårlige), 3) hvad det koster, "
        "4) prioriteret handlingsliste (maks 5).",
    ])


def forklar(analysis: dict, caller: Optional[Callable[[str, str], str]] = None) -> dict:
    if analysis.get("error"):
        return {"error": analysis["error"]}
    if caller is None:
        caller = vertex_gemini_caller()
    prompt = _byg(analysis)
    return {"forklaring_tekst": caller(SYSTEM, prompt), "prompt_brugt": prompt,
            "model": "gemini (vertex)", "note": "LLM-tekst ud fra de deterministiske review-tal."}
