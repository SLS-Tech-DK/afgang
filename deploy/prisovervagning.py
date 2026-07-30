"""
SLS Tech · Afgang — Prisovervågning (recurring)
-----------------------------------------------
Overvåger konkurrenters priser over tid og alarmerer ved ændringer.
Input: prissnapshots (egen + konkurrenter) pr. produkt, over tid.

To kernefunktioner:
  - prisposition: hvor ligger egen pris ift. konkurrenter, pr. produkt (billigst/dyrest).
  - ændringsdetektion: sammenlign to snapshots → hvad ændrede sig + alarmer.

ÆRLIG ARKITEKTUR-GRÆNSE:
Selve prisindsamlingen (skrabe konkurrentsider) sker via et injicerbart
fetcher-interface — mock i test, rigtig scraping ved deployment.
  - Deterministisk positions-/ændringskerne: testet.
  - Live scraping: UTESTET indtil fetcher er wired.

Et snapshot er: {"product": str, "own": float|None, "competitors": {navn: pris}}.
"""

from __future__ import annotations
from typing import Callable, Optional


def _round(x, n=2):
    return round(x + 0.0, n)


def price_position(snapshot: list[dict]) -> list[dict]:
    """Pr. produkt: er egen pris billigst/dyrest, og hvad er billigste konkurrent."""
    out = []
    for row in snapshot:
        own = row.get("own")
        comps = {k: v for k, v in (row.get("competitors") or {}).items() if v is not None}
        entry = {"product": row["product"], "own": own}
        if comps:
            cheapest = min(comps.items(), key=lambda x: x[1])
            dearest = max(comps.items(), key=lambda x: x[1])
            entry["cheapest_competitor"] = {"name": cheapest[0], "price": _round(cheapest[1])}
            entry["dearest_competitor"] = {"name": dearest[0], "price": _round(dearest[1])}
            if own is not None:
                below = [c for c, p in comps.items() if own < p]
                above = [c for c, p in comps.items() if own > p]
                entry["position"] = ("billigst" if not above else
                                     "dyrest" if not below else "midt")
                entry["gap_to_cheapest"] = _round(own - cheapest[1])
        out.append(entry)
    return out


def detect_changes(previous: list[dict], current: list[dict], threshold_pct: float = 1.0) -> list[dict]:
    """Sammenlign to snapshots → alarmer ved prisændringer over threshold_pct."""
    def index(snap):
        idx = {}
        for row in snap:
            idx[row["product"]] = row.get("competitors") or {}
            idx[(row["product"], "_own")] = row.get("own")
        return idx
    pi, ci = index(previous), index(current)
    alerts = []
    for row in current:
        prod = row["product"]
        prev_comps = pi.get(prod, {})
        for comp, new_price in (row.get("competitors") or {}).items():
            old_price = prev_comps.get(comp)
            if old_price is None or new_price is None or old_price == 0:
                continue
            change_pct = (new_price - old_price) / old_price * 100
            if abs(change_pct) >= threshold_pct:
                alerts.append({
                    "product": prod, "competitor": comp,
                    "old_price": _round(old_price), "new_price": _round(new_price),
                    "change_pct": _round(change_pct, 1),
                    "direction": "op" if change_pct > 0 else "ned",
                })
    alerts.sort(key=lambda a: abs(a["change_pct"]), reverse=True)
    return alerts


def recommendations(positions: list[dict], alerts: list[dict]) -> list[str]:
    recs = []
    dyrest = [p for p in positions if p.get("position") == "dyrest"]
    if dyrest:
        recs.append(f"{len(dyrest)} varer hvor du er dyrest — overvej prisjustering eller tydeliggør merværdi.")
    drops = [a for a in alerts if a["direction"] == "ned"]
    if drops:
        d = drops[0]
        recs.append(f"'{d['competitor']}' sænkede prisen på {d['product']} med {abs(d['change_pct'])}% — reager hvis du vil matche.")
    rises = [a for a in alerts if a["direction"] == "op"]
    if rises:
        r = rises[0]
        recs.append(f"'{r['competitor']}' hævede prisen på {r['product']} — du kan evt. tjene mere uden at miste position.")
    return recs[:5]


def analyze(current: list[dict], previous: Optional[list[dict]] = None, threshold_pct: float = 1.0) -> dict:
    positions = price_position(current)
    alerts = detect_changes(previous, current, threshold_pct) if previous else []
    return {
        "meta": {"products": len(current), "has_previous": previous is not None,
                 "threshold_pct": threshold_pct},
        "positions": positions,
        "alerts": alerts,
        "recommendations": recommendations(positions, alerts),
    }


# --- Prisindsamling (interface) ---------------------------------------------
def collect_snapshot(products: list[str], own_urls: dict, competitor_urls: dict,
                     fetcher: Optional[Callable[[str], float]] = None) -> list[dict]:
    """Byg et snapshot ved at hente priser. `fetcher(url)->pris` wires til rigtig
    scraping ved deployment. UTESTET mod live sider her.
    own_urls: {product: url}. competitor_urls: {competitor: {product: url}}."""
    if fetcher is None:
        raise NotImplementedError("Live fetcher ikke wired — injicér fetcher (scraping).")
    snap = []
    for p in products:
        comps = {}
        for comp, urls in competitor_urls.items():
            if p in urls:
                comps[comp] = fetcher(urls[p])
        snap.append({"product": p, "own": fetcher(own_urls[p]) if p in own_urls else None,
                     "competitors": comps})
    return snap
