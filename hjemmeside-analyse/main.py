#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
afgang Hjemmeside-analyse — Cloud Run HTTP-service (motoren bag one-click).

Flow:  GET /analyse?url=<side>&mode=demo|client&preview=1
  fetch_site (netværk, kører her på Cloud Run)  ->  analyze (lag 1)
  ->  lang_layer (lag 2, Gemini, hvis GEMINI_API_KEY er sat)  ->  generator  ->  HTML
  preview=1 returnerer kun score + top-3 anbefalinger (JSON) til gratis forhåndsvisning.

Nøgler: GEMINI_API_KEY sættes som miljøvariabel ved deploy (fra Bitwarden) — aldrig i koden.
Kør lokalt:  GEMINI_API_KEY=… python3 main.py   (PORT default 8080)
"""
from __future__ import annotations
import importlib.util
import json
import os
from bs4 import BeautifulSoup
from flask import Flask, request, Response

from fetch_site import fetch_site
from analyze import analyze
from lang_layer import language_findings

# generatoren har bindestreg i filnavnet → indlæs eksplicit
_spec = importlib.util.spec_from_file_location("generator", os.path.join(os.path.dirname(__file__), "GENERATOR-hjemmeside-analyse.py"))
generator = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(generator)

app = Flask(__name__)


def _page_texts(site: dict) -> list[dict]:
    out = []
    base = site.get("base_url", "")
    for p in site.get("pages", []):
        soup = BeautifulSoup(p.get("html", ""), "html.parser")
        for t in soup(["script", "style", "noscript"]):
            t.extract()
        out.append({"path": (p["url"].replace(base, "") or "/"), "text": soup.get_text(" ", strip=True)})
    return out


def run_analysis(url: str, name: str = "", type: str = "", tech: str = "", use_lang: bool = True) -> dict:
    """Fuld motor: URL -> payload (lag 1 + evt. lag 2). Ren returværdi, ingen HTTP."""
    site = fetch_site(url, name=name, type=type, tech=tech)
    payload = analyze(site, {"name": name or site.get("name", ""), "type": type})
    if use_lang and os.environ.get("GEMINI_API_KEY"):
        rows = language_findings(_page_texts(site))
        if rows:
            payload["sprog_rows"] = rows
            # medregn sprogfejl i tælleren
            n = sum(len(r[1].split("·")) for r in rows)
            payload["meta"]["counts"].insert(0, {"n": f"{n}", "l": "sprogfund", "c": "rod"})
    return payload


def handle(url: str, mode: str = "demo", preview: bool = False,
           name: str = "", type: str = "", tech: str = ""):
    """Testbar kerne bag HTTP-endpointet. Returnerer (body, mimetype, status)."""
    if not url:
        return (json.dumps({"error": "mangler ?url="}), "application/json", 400)
    payload = run_analysis(url, name=name, type=type, tech=tech)
    payload.pop("_findings", None)
    if preview:
        prev = {"score": payload["meta"]["score"],
                "top": [{"title": r["title"], "tag": r["tag_label"]} for r in payload["recommendations"][:3]]}
        return (json.dumps(prev, ensure_ascii=False), "application/json", 200)
    html = generator.build(payload, "client" if mode == "client" else "demo")
    return (html, "text/html; charset=utf-8", 200)


@app.get("/analyse")
def analyse():
    body, mime, status = handle(
        url=request.args.get("url", "").strip(),
        mode=request.args.get("mode", "demo"),
        preview=request.args.get("preview") in ("1", "true", "yes"),
        name=request.args.get("name", ""),
        type=request.args.get("type", ""),
        tech=request.args.get("tech", ""),
    )
    return Response(body, status=status, mimetype=mime.split(";")[0], headers={"Content-Type": mime})


@app.get("/health")
def health():
    return {"ok": True}


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
