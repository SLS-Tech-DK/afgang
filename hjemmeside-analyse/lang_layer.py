#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
afgang Hjemmeside-analyse — lag 2 (sprog/stavefejl via sprogmodel).

Kundevendt/B2C → Gemini (SLS-regel). Nøglen læses fra miljøvariablen GEMINI_API_KEY
(sættes ved deploy fra Bitwarden — ALDRIG hardkodet i koden).

Kontrakt: `language_findings(pages) -> list[[side, fund]]` (sprog_rows til payloaden).
Hvis nøglen mangler, eller kaldet fejler: returnér [] og lad resten af analysen køre videre.
Aldrig "stak" — altid "stack".
"""
from __future__ import annotations
import json
import os
import re

GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-3.6-flash")
GEMINI_ENDPOINT = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
MAX_PAGES = 15
MAX_CHARS = 4000  # pr. side, så prompten ikke løber løbsk

SYSTEM = (
    "Du er dansk korrekturlæser for en hjemmeside. Find KONKRETE stave- og sprogfejl "
    "(forkerte ord, manglende sammensætninger, dobbelt-ord, engelsk i dansk tekst). "
    "Ikke stil-smag, kun tydelige fejl. Svar KUN med JSON: en liste af objekter "
    '{"fund": "<fejl → rettelse, kort>"}. Maks 6 pr. side. Brug ordet "stack", aldrig "stak".'
)


def _extract_json(txt: str):
    """Robust: accepter (a) JSON-array, (b) løse {...}-objekter linje for linje, (c) kodeblok.
    Modellen svarer ikke altid med [ ]-array — så vi falder tilbage til at samle enkelt-objekter."""
    if not txt:
        return []
    txt = txt.replace("```json", "").replace("```", "")
    m = re.search(r"\[.*\]", txt, flags=re.S)
    if m:
        try:
            return json.loads(m.group(0))
        except Exception:
            pass
    out = []
    for obj in re.findall(r"\{[^{}]*\}", txt, flags=re.S):
        try:
            out.append(json.loads(obj))
        except Exception:
            continue
    return out


def _analyze_page(session, api_key: str, path: str, text: str) -> list[str]:
    body = {
        "system_instruction": {"parts": [{"text": SYSTEM}]},
        "contents": [{"parts": [{"text": f"Side: {path}\n\nTekst:\n{text[:MAX_CHARS]}"}]}],
        "generationConfig": {"temperature": 0, "maxOutputTokens": 800},
    }
    url = GEMINI_ENDPOINT.format(model=GEMINI_MODEL)
    r = session.post(url, params={"key": api_key}, json=body, timeout=30)
    r.raise_for_status()
    data = r.json()
    try:
        txt = data["candidates"][0]["content"]["parts"][0]["text"]
    except Exception:
        return []
    out = []
    for item in _extract_json(txt):
        if isinstance(item, dict) and item.get("fund"):
            out.append(str(item["fund"]))
        elif isinstance(item, str):
            out.append(item)
    return out[:6]


def language_findings(pages: list[dict], api_key: str | None = None) -> list[list[str]]:
    """pages: [{"path" eller "url": str, "text": str}]. Returnér sprog_rows [[side, "fund; fund"]]."""
    api_key = api_key or os.environ.get("GEMINI_API_KEY")
    if not api_key:
        return []  # ingen nøgle → spring laget over, resten kører videre
    try:
        import requests
    except Exception:
        return []
    session = requests.Session()
    rows: list[list[str]] = []
    for p in pages[:MAX_PAGES]:
        path = p.get("path") or p.get("url") or "?"
        text = (p.get("text") or "").strip()
        if len(text) < 40:
            continue
        try:
            found = _analyze_page(session, api_key, path, text)
        except Exception:
            continue
        if found:
            rows.append([path, " · ".join(found)])
    return rows


if __name__ == "__main__":
    # lille røgtest uden netværk: uden nøgle skal den returnere [] uden at kaste
    os.environ.pop("GEMINI_API_KEY", None)
    assert language_findings([{"path": "/", "text": "en lang nok tekst til at blive vurderet af modellen her"}]) == []
    print("lang_layer: ingen nøgle -> [] (OK, ingen crash)")
