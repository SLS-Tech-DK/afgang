"""
SLS Tech · Afgang — URL-sti → produkt-type mapping.
---------------------------------------------------
Holdes adskilt fra main.py (ingen motor-imports) så mapping-logikken kan
enhedstestes uden at loade alle motorer.

Formål: hvert produkt og delelement har sin EGEN URL-sti, så købsflowet kan
ramme præcis det rigtige produkt:
    POST /salgsanalyse      → type "salgsanalyse"
    POST /butiksanalyse     → type "butiksanalyse" (premium-samling)
    POST /ai-synlighed      → type "ai_synlighed"
Bagud-kompatibelt: {"type": "..."} i body virker stadig og vinder over stien.

Stier accepteres fleksibelt: store/små bogstaver, '-' og '_' er ombyttelige,
danske varianter (fx /prisovervaagning og /prisovervagning) peger samme sted.
"""
from __future__ import annotations

# Kanoniske typer (skal matche REGISTRY i main.py).
CANONICAL = {
    "salgsanalyse", "indkobsanalyse", "lageranalyse", "kundeanalyse",
    "butiksanalyse", "konkurrentanalyse", "ai_synlighed", "prisovervagning",
    "naevner_ai_alarm", "produkttekst", "review_analyse", "landingsside",
    "annonce_spild", "soegeords_gap",
}

# Ekstra sti-aliaser (kunde-/URL-venlige navne) → kanonisk type.
# Nøgler skrives normaliseret (kun a-z0-9, se _norm).
ALIASES = {
    # danske æøå-varianter og pæne navne
    "indkoebsanalyse": "indkobsanalyse",
    "prisovervaagning": "prisovervagning",
    "prisovervaging": "prisovervagning",
    "naevneraialarm": "naevner_ai_alarm",
    "blivergnaevnt": "naevner_ai_alarm",       # /bliver-jeg-naevnt uden 'jeg'
    "bliverjegnaevnt": "naevner_ai_alarm",
    "soegeordsgap": "soegeords_gap",
    "sogeordsgap": "soegeords_gap",
    "aisynlighed": "ai_synlighed",
    "reviewanalyse": "review_analyse",
    "annoncespild": "annonce_spild",
    # kælenavn for premium-samlingen
    "butiksrontgen": "butiksanalyse",
    "butiksroentgen": "butiksanalyse",
}


def _norm(s: str) -> str:
    """Til sammenligning: kun a-z0-9. '-' og '_' fjernes, så de er ombyttelige."""
    return "".join(ch for ch in (s or "").strip().lower() if ch.isalnum())


# Forud-normaliseret opslag: kanonisk-type-uden-underscore → kanonisk type.
_CANON_NORM = {_norm(t): t for t in CANONICAL}


def path_to_type(path: str) -> str | None:
    """Udled produkt-type af en URL-sti. Returnér None hvis stien ikke matcher
    et produkt (fx '/', '/health'). Tager kun FØRSTE sti-segment."""
    if not path:
        return None
    seg = path.strip("/").split("/", 1)[0]
    key = _norm(seg)
    if not key:
        return None
    if key in _CANON_NORM:
        return _CANON_NORM[key]
    return ALIASES.get(key)


def resolve_type(body: dict, path: str) -> str | None:
    """Body-'type' vinder (bagud-kompatibelt); ellers udled af stien."""
    t = (body or {}).get("type")
    if t:
        return t
    return path_to_type(path)
