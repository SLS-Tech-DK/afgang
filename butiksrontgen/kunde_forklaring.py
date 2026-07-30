"""Gemini-forklaringslag til Kundeanalyse. Samme caller-mønster (Vertex/mock).
Live Vertex-kald: UTESTET indtil nøgle ved deployment."""
from __future__ import annotations
import json
from typing import Callable, Optional
from gemini_forklaring import vertex_gemini_caller

SYSTEM_INSTRUKTION = (
    "Du er en nøgtern dansk kundeanalytiker for SLS Tech. Du får en FÆRDIG "
    "analyse af en webshops kundedata. Forklar hvem der tjener butikken penge, "
    "hvem der er ved at forsvinde, og hvad man skal gøre. REGLER: brug KUN "
    "tallene nedenfor, opfind aldrig tal. Kort, konkret, dansk. Afslut med en "
    "prioriteret handlingsliste (maks 5)."
)


def _byg_prompt(a: dict) -> str:
    m = a.get("meta", {})
    dele = [
        f"{m.get('distinct_customers')} kunder, frem til {m.get('reference_date')}, {m.get('rows_used')} linjer.",
        ("ADVARSLER: " + "; ".join(m.get("warnings", []))) if m.get("warnings") else "",
        "TOP KUNDER (livstidsværdi):", json.dumps(a.get("clv", []), ensure_ascii=False, default=str),
        "RFM (recency/frequency/monetary):", json.dumps(a.get("rfm", []), ensure_ascii=False, default=str),
        "CHURN-SIGNAL (kunder der er forsvundet):", json.dumps(a.get("churn_signal", []), ensure_ascii=False, default=str),
        "SEGMENTER:", json.dumps(a.get("segments", {}), ensure_ascii=False, default=str),
        "Skriv: 1) resumé, 2) hvem driver omsætningen, 3) hvem er ved at churne og hvad gør man, 4) prioriteret handlingsliste (maks 5).",
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
