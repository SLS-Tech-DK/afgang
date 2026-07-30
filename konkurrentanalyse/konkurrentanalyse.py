"""
SLS Tech · Afgang — Konkurrentanalyse-motor
-------------------------------------------
Input: kundens domæne + op til 3 konkurrenter.
Output: side-om-side på pris/sortiment/trafik/synlighed, gaps, og en
prioriteret "hvor du kan vinde"-liste.

VIGTIG ARKITEKTUR-GRÆNSE (ærlig):
Selve dataindsamlingen (skrabe konkurrentsider, trafik-estimat, SEO/AI-
synlighed) sker UDEFRA og wires til rigtige kilder ved deployment via
`collect`-interfacet. Denne fil indeholder:
  1) en normaliseret data-kontrakt (hvad hver aktør skal beskrives med)
  2) den DETERMINISTISKE sammenlignings-/scoringskerne (testet)
  3) et collect()-interface med injicerbar fetcher (mock i test, rigtig ved deploy)

Deterministisk kerne = testet. Live fetch = UTESTET indtil kilder er wired.
"""

from __future__ import annotations
import json
from typing import Callable, Optional

# --- Data-kontrakt -----------------------------------------------------------
# Hver aktør (egen + konkurrenter) beskrives med samme felter. Ukendt = None.
#   name: str
#   avg_price: float | None        (gns. produktpris, DKK)
#   product_count: int | None      (sortimentsbredde)
#   traffic_estimate: int | None   (est. månedlige besøg)
#   ai_visibility: float | None    (0-100, hvor ofte nævnt i AI-svar — fra AI-synlighedsmotoren)
#   shipping_free_over: float|None (fri fragt-grænse, DKK; lavere = bedre for kunden)

FIELDS = ["avg_price", "product_count", "traffic_estimate", "ai_visibility", "shipping_free_over"]
# retning: True = højere er bedre for aktøren; False = lavere er bedre
BETTER_HIGH = {"product_count": True, "traffic_estimate": True, "ai_visibility": True,
               "avg_price": False, "shipping_free_over": False}


def _rank_field(actors, field):
    """Returnér {name: placering} for et felt (1 = bedst). Ignorér None."""
    vals = [(a["name"], a.get(field)) for a in actors if a.get(field) is not None]
    if not vals:
        return {}
    vals.sort(key=lambda x: x[1], reverse=BETTER_HIGH[field])
    return {name: i + 1 for i, (name, _) in enumerate(vals)}


def side_by_side(own, competitors):
    actors = [own] + competitors
    table = {"actors": [a["name"] for a in actors], "fields": {}}
    for f in FIELDS:
        table["fields"][f] = {a["name"]: a.get(f) for a in actors}
    return table


def gaps(own, competitors):
    """Hvor ligger egen aktør bagud/foran ift. bedste konkurrent pr. felt."""
    out = []
    for f in FIELDS:
        comp_vals = [c.get(f) for c in competitors if c.get(f) is not None]
        ov = own.get(f)
        if ov is None or not comp_vals:
            continue
        best_comp = max(comp_vals) if BETTER_HIGH[f] else min(comp_vals)
        ahead = (ov >= best_comp) if BETTER_HIGH[f] else (ov <= best_comp)
        out.append({"field": f, "own": ov, "best_competitor": best_comp,
                    "status": "foran" if ahead else "bagud",
                    "gap": _round(abs(ov - best_comp))})
    return out


def where_to_win(own, competitors):
    """Prioriteret liste: felter hvor egen aktør er bagud og gap er størst =
    de bedste steder at rykke. Kun 'bagud'-felter, sorteret efter relativ gap."""
    g = [x for x in gaps(own, competitors) if x["status"] == "bagud"]
    def rel(x):
        base = max(abs(x["best_competitor"]), 1e-9)
        return x["gap"] / base
    g.sort(key=rel, reverse=True)
    labels = {"avg_price": "Din gennemsnitspris er højere — overvej at justere eller tydeliggøre værdi.",
              "product_count": "Dit sortiment er smallere — udvid i de kategorier konkurrenterne dækker.",
              "traffic_estimate": "Du får mindre trafik — styrk SEO/AI-synlighed og markedsføring.",
              "ai_visibility": "Du nævnes sjældnere i AI-svar — kør AEO-optimering (se AI-synlighedsproduktet).",
              "shipping_free_over": "Din fri fragt-grænse er højere — sænk den for at matche konkurrenterne."}
    return [{"field": x["field"], "gap": x["gap"], "action": labels.get(x["field"], "")} for x in g]


def analyze(own: dict, competitors: list[dict]) -> dict:
    if not own or not own.get("name"):
        return {"error": "Mangler egen aktør (name)."}
    competitors = competitors or []
    return {
        "meta": {"own": own["name"], "competitors": [c.get("name") for c in competitors],
                 "n_competitors": len(competitors)},
        "side_by_side": side_by_side(own, competitors),
        "gaps": gaps(own, competitors),
        "where_to_win": where_to_win(own, competitors),
    }


# --- Data-indsamling (interface) --------------------------------------------
def collect(domain: str, competitor_domains: list[str],
            fetcher: Optional[Callable[[str], dict]] = None) -> tuple[dict, list[dict]]:
    """Indsaml normaliserede data for domæne + konkurrenter.
    `fetcher(domain) -> dict` wires til rigtig scraping/SEO-API/AI-synlighed ved
    deployment. UTESTET mod live kilder her. I test injiceres en mock-fetcher."""
    if fetcher is None:
        raise NotImplementedError("Live fetcher ikke wired endnu — injicér fetcher (scraping/SEO-API/AI-synlighed).")
    own = {"name": domain, **fetcher(domain)}
    comps = [{"name": d, **fetcher(d)} for d in competitor_domains]
    return own, comps


def _round(x, n=2):
    return round(x + 0.0, n)


if __name__ == "__main__":
    print("Konkurrentanalyse-motor. Kør test_konk.py for demo.")
