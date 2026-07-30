"""
SLS Tech · Afgang — Landingsside-teardown
-----------------------------------------
Input: sidetekst/HTML for én landingsside.
Output: konverterings-kritik — deterministiske tjek af de vigtigste elementer
(overskrift, værditilbud, CTA, trust-signaler, kontakt, mobil-hints) + score
+ prioriterede anbefalinger.
Nuanceret tekstkritik = Gemini (interface). Her tjekkes deterministisk.
"""
from __future__ import annotations
import re


def _round(x, n=0):
    return round(x + 0.0, n)


def audit(page_text: str) -> dict:
    t = page_text or ""
    tl = t.lower()
    checks = {
        "har_overskrift": bool(re.search(r"(?m)^\s*#{1,3}\s+\S", t)) or bool(re.search(r"<h1[^>]*>.*?</h1>", tl, re.S)),
        "har_cta": any(k in tl for k in ["køb", "koeb", "bestil", "book", "tilmeld", "start", "prøv", "proev", "kom i gang", "kontakt", "add to cart", "buy"]),
        "har_vaerditilbud": bool(re.search(r"(spar|gratis|hurtig|nem|garanti|bedst|billig|kvalitet|levering)", tl)),
        "har_trust_signaler": any(k in tl for k in ["anmeldelse", "review", "trustpilot", "kunder", "garanti", "sikker", "certifi", "tilfredshed"]),
        "har_kontakt": any(k in tl for k in ["kontakt", "telefon", "email", "e-mail", "@", "tlf"]),
        "har_konkrete_tal": bool(re.search(r"\d", t)),
        "ikke_for_lang_uden_struktur": (len(t.split()) < 400) or bool(re.search(r"(?m)^\s*[-*#]", t)) or ("<h" in tl) or ("<ul" in tl),
    }
    passed = sum(checks.values())
    score = _round(passed / len(checks) * 100)
    tips = {
        "har_overskrift": "Tilføj én tydelig hovedoverskrift (H1) der siger hvad man får.",
        "har_cta": "Tilføj en klar call-to-action-knap (fx 'Køb nu', 'Book tid').",
        "har_vaerditilbud": "Gør værditilbuddet eksplicit — hvorfor vælge jer? (fri fragt, garanti, hurtig levering).",
        "har_trust_signaler": "Tilføj trust-signaler: anmeldelser, garanti, antal kunder.",
        "har_kontakt": "Vis kontaktinfo tydeligt — det øger tillid.",
        "har_konkrete_tal": "Brug konkrete tal (priser, leveringstid, antal) — vagt sælger ikke.",
        "ikke_for_lang_uden_struktur": "Bryd lange tekstblokke op med overskrifter og punktlister.",
    }
    anbefalinger = [tips[k] for k, v in checks.items() if not v]
    return {"checks": checks, "score": score, "anbefalinger": anbefalinger}


def analyze(page_text: str, page_name: str = "landingsside") -> dict:
    a = audit(page_text)
    return {"meta": {"page": page_name, "words": len((page_text or "").split())}, **a}
