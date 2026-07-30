"""
SLS Tech · Afgang — "Nævner AI min virksomhed"-alarm (recurring)
----------------------------------------------------------------
Månedligt tjek: nævner de store AI-modeller kundens virksomhed, når folk
spørger om branchen? Alarmerer når synligheden flytter sig vs. sidste måned,
og når en konkurrent rykker frem.

Bygger oven på GEO-motoren fra ai_synlighed. Selve AI-forespørgslerne wires
via ai_synlighed.run_queries (mock i test, Gemini/Vertex ved deployment).

Deterministisk sammenlignings-/alarmkerne: testet.
Live model-forespørgsler: UTESTET indtil querier er wired.

Et gemt "målepunkt" er outputtet fra ai_synlighed.geo_visibility (dict).
"""

from __future__ import annotations
from ai_synlighed import geo_visibility


def _round(x, n=1):
    return round(x + 0.0, n)


def compare(current: dict, previous: dict | None, threshold_pp: float = 5.0) -> dict:
    """Sammenlign denne måneds synlighed med sidste. threshold_pp = procentpoint
    ændring før der alarmeres."""
    cur_rate = current.get("brand_mention_rate_pct", 0)
    cur_sov = current.get("share_of_voice_pct", 0)
    alerts = []
    deltas = {}
    if previous:
        prev_rate = previous.get("brand_mention_rate_pct", 0)
        prev_sov = previous.get("share_of_voice_pct", 0)
        d_rate = _round(cur_rate - prev_rate)
        d_sov = _round(cur_sov - prev_sov)
        deltas = {"mention_rate_delta_pp": d_rate, "share_of_voice_delta_pp": d_sov}
        if abs(d_rate) >= threshold_pp:
            alerts.append({"type": "mention_rate", "direction": "op" if d_rate > 0 else "ned",
                           "change_pp": d_rate,
                           "besked": f"Din AI-omtale er gået {'op' if d_rate>0 else 'ned'} med {abs(d_rate)} procentpoint siden sidste måling."})
        if abs(d_sov) >= threshold_pp:
            alerts.append({"type": "share_of_voice", "direction": "op" if d_sov > 0 else "ned",
                           "change_pp": d_sov,
                           "besked": f"Din share-of-voice vs. konkurrenter er gået {'op' if d_sov>0 else 'ned'} med {abs(d_sov)} procentpoint."})
        # konkurrent der rykker frem
        prev_comp = previous.get("competitor_mentions", {})
        for comp, cnt in current.get("competitor_mentions", {}).items():
            old = prev_comp.get(comp, 0)
            if cnt > old and cnt > current.get("brand_mentions", 0):
                alerts.append({"type": "competitor_gain", "competitor": comp,
                               "besked": f"'{comp}' nævnes nu oftere end dig og er steget siden sidst — hold øje."})
    else:
        alerts.append({"type": "baseline",
                       "besked": "Første måling registreret — næste måned kan vi vise ændringer."})
    return {"current": {"brand_mention_rate_pct": cur_rate, "share_of_voice_pct": cur_sov},
            "deltas": deltas, "alerts": alerts, "alarm": bool([a for a in alerts if a["type"] != "baseline"])}


def run_check(query_results: list[dict], brand: str, competitors: list[str],
              previous_measurement: dict | None = None, threshold_pp: float = 5.0) -> dict:
    """Kør månedens tjek: mål synlighed nu, sammenlign med sidste måling.
    Gem returnerede 'measurement' til næste måned."""
    measurement = geo_visibility(query_results, brand, competitors)
    cmp = compare(measurement, previous_measurement, threshold_pp)
    return {"brand": brand, "measurement": measurement, "comparison": cmp}
