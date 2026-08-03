"""Gemini-forklaringslag til Fuld Butiksanalyse. Samler de fire delanalysers
nøglefund + krydsanalyser til én sammenhængende dansk direktør-plan.
Live Vertex UTESTET indtil deploy."""
from __future__ import annotations
import json
from typing import Callable, Optional
from gemini_forklaring import vertex_gemini_caller

SYSTEM = ("Du er en nøgtern dansk butiks-/e-handelsrådgiver. Du får en FÆRDIG samlet "
          "butiksanalyse (salg, indkøb, lager, kunder + krydsanalyser). Skriv én "
          "sammenhængende, prioriteret handlingsplan en travl ejer kan handle på i denne uge. "
          "Brug KUN tallene nedenfor, opfind intet. Kort, dansk, konkret, maks 7 punkter.")


def _byg(a: dict) -> str:
    m = a.get("meta", {})
    salg = a.get("salgsanalyse", {})
    dele = [
        f"NØGLETAL: omsætning {m.get('total_revenue')} kr, {m.get('distinct_orders')} ordrer, "
        f"{m.get('distinct_products')} produkter, gns. ordre {m.get('avg_order_value')} kr.",
        f"BESTSELLERE: {json.dumps(salg.get('bestsellers', {}).get('by_revenue', [])[:5], ensure_ascii=False)}",
        f"KØBES-SAMMEN: {json.dumps(salg.get('co_purchase', []), ensure_ascii=False)}",
        f"KANNIBALISERING: {json.dumps(a.get('kryds', {}).get('kannibalisering', [])[:5], ensure_ascii=False)}",
        f"MARGIN PÅ TVÆRS: {json.dumps(a.get('kryds', {}).get('margin_paa_tvaers', {}), ensure_ascii=False)[:1200]}",
        f"DØDVARER: {json.dumps(a.get('lageranalyse', {}).get('deadstock', [])[:5], ensure_ascii=False)}",
        f"GENBESTIL: {json.dumps(a.get('indkobsanalyse', {}).get('reorder_list', [])[:5], ensure_ascii=False)}",
        f"KUNDER: {json.dumps(a.get('kundeanalyse', {}).get('segments', {}), ensure_ascii=False)}",
        f"DETERMINISTISK UDKAST-PLAN: {json.dumps(a.get('handlingsplan', []), ensure_ascii=False)}",
        "Skriv den samlede prioriterede handlingsplan (maks 7), vigtigst først.",
    ]
    return "\n".join(dele)


def forklar(analysis: dict, caller: Optional[Callable[[str, str], str]] = None) -> dict:
    if analysis.get("error"):
        return {"error": analysis["error"]}
    if caller is None:
        caller = vertex_gemini_caller()
    prompt = _byg(analysis)
    return {"forklaring_tekst": caller(SYSTEM, prompt), "prompt_brugt": prompt,
            "model": "gemini (vertex)", "note": "LLM-plan ud fra de samlede deterministiske tal."}
