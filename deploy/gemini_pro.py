"""
SLS Tech · Afgang — stærk, grounded Gemini-caller (tung tier).
Bruges af analyser der går på nettet og kræver rigtig syntese (fx
konkurrentanalyse). Default model = gemini-2.5-pro (via env KONK_MODEL),
kører på Vertex ligesom flash-laget. Returnerer parset JSON.

Live Vertex-kald UTESTET i sandbox — verificér ved deploy (samme metode som
flash: bekræft at modellen findes i VERTEX_LOCATION-regionen).
"""
from __future__ import annotations
import os, re, json
from typing import Callable, Optional


def _extract_json(text: str):
    """Robust: find første {...}-blok, tolerer ```json-fences."""
    if not text:
        return None
    t = text.strip()
    t = re.sub(r"^```(?:json)?\s*|\s*```$", "", t, flags=re.I).strip()
    try:
        return json.loads(t)
    except Exception:
        pass
    m = re.search(r"\{.*\}", t, re.S)
    if m:
        try:
            return json.loads(m.group(0))
        except Exception:
            return None
    return None


def vertex_pro_caller(model: Optional[str] = None) -> Callable[[str, str], str]:
    """Live Vertex-caller med stærk model. (system, prompt) -> rå tekst."""
    def _call(system: str, prompt: str) -> str:
        mdl = model or os.environ.get("KONK_MODEL", "gemini-2.5-pro")
        import vertexai
        from vertexai.generative_models import GenerativeModel
        project = os.environ.get("GOOGLE_CLOUD_PROJECT")
        location = os.environ.get("VERTEX_LOCATION", "europe-west4")
        vertexai.init(project=project, location=location)
        gm = GenerativeModel(mdl, system_instruction=system)
        resp = gm.generate_content(prompt, generation_config={"temperature": 0.2})
        return resp.text
    return _call


def call_json(system: str, prompt: str, caller: Optional[Callable[[str, str], str]] = None) -> dict:
    """Kald model, forvent JSON, returnér parset dict eller {'_raw':...}."""
    if caller is None:
        caller = vertex_pro_caller()
    raw = caller(system, prompt)
    parsed = _extract_json(raw)
    return parsed if isinstance(parsed, dict) else {"_raw": raw, "_parse_error": True}
