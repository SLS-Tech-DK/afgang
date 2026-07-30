"""Gemini-forklaringslag til Lageranalyse. Samme caller-mønster (Vertex/mock).
Live Vertex-kald: UTESTET indtil nøgle ved deployment."""
from __future__ import annotations
import json
from typing import Callable, Optional
from gemini_forklaring import vertex_gemini_caller

SYSTEM_INSTRUKTION = (
    "Du er en nøgtern dansk lagerrådgiver for SLS Tech. Du får en FÆRDIG "
    "analyse af en webshops salgshistorik (og evt. lagerdata). Forklar hvor "
    "kapital og plads bindes, hvad der er dødvarer, og hvad man skal rydde ud i. "
    "REGLER: brug KUN tallene nedenfor, opfind aldrig tal. Kort, konkret, dansk. "
    "Afslut med en prioriteret oprydningsliste (maks 5)."
)


def _byg_prompt(a: dict) -> str:
    m = a.get("meta", {})
    dele = [
        f"PERIODE frem til {m.get('reference_date')} ({m.get('span_days')} dage), {m.get('rows_used')} linjer.",
        ("ADVARSLER: " + "; ".join(m.get("warnings", []))) if m.get("warnings") else "",
        "DØDVARER (intet salg længe):", json.dumps(a.get("deadstock", []), ensure_ascii=False, default=str),
        "LANGSOMTSÆLGENDE:", json.dumps(a.get("slow_movers", []), ensure_ascii=False, default=str),
        "SÆSON (omsætning pr. måned):", json.dumps(a.get("seasonality", []), ensure_ascii=False, default=str),
        "KAPITALBINDING:", json.dumps(a.get("capital_tied", {}), ensure_ascii=False, default=str),
        "Skriv: 1) resumé, 2) hvor bindes kapital/plads, 3) dødvarer at rydde ud, 4) prioriteret oprydningsliste (maks 5).",
    ]
    return "\n".join(d for d in dele if d)


def forklar(analysis: dict, caller: Optional[Callable[[str, str], str]] = None) -> dict:
    if analysis.get("error"):
        return {"error": analysis["error"]}
    if caller is None:
        caller = vertex_gemini_caller()
    prompt = _byg_prompt(analysis)
    return {"forklaring_tekst": caller(SYSTEM_INSTRUKTION, prompt), "prompt_brugt": prompt,
            "model": "gemini (vertex)", "note": "LLM-tekst ud fra deterministiske tal."}
