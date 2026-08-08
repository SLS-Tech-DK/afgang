"""Test af Cloud Function-routeren: rigtige typer ruter til rigtige motorer,
ukendt type fejler pænt, deterministisk resultat kommer igennem."""
import io, csv
from main import route, REGISTRY

ok = True

# alle typer er registreret
expected = {"salgsanalyse","indkobsanalyse","lageranalyse","kundeanalyse","butiksanalyse",
            "konkurrentanalyse","ai_synlighed","prisovervagning","naevner_ai_alarm",
            "produkttekst","review_analyse","landingsside","annonce_spild","soegeords_gap",
            "fuld_butiksanalyse","spoerg_data"}
if set(REGISTRY) != expected:
    ok = False; print("FEJL: registry mangler typer:", expected ^ set(REGISTRY))

# ukendt type
r = route({"type": "findes_ikke"})
if r["ok"] or "Ukendt type" not in r["error"]:
    ok = False; print("FEJL: ukendt type burde fejle pænt")

# salgsanalyse via router (to-fil-model: vare + ordre)
import webshop_suite as _ws
r = route({"type": "salgsanalyse", "vare_csv": _ws.SAMPLE_VARE, "ordre_csv": _ws.SAMPLE_ORDRE})
if not r["ok"] or r["type"] != "salgsanalyse" or "html" not in r["result"] or "analyse" not in r["result"]:
    ok = False; print("FEJL: salgsanalyse-routing")

# salgsanalyse demo (ægte teaser) -> kun html, ingen rådata (IP-sikker)
r = route({"type": "salgsanalyse", "demo": True, "vare_csv": _ws.SAMPLE_VARE, "ordre_csv": _ws.SAMPLE_ORDRE})
if not r["ok"] or "html" not in r["result"] or any(k in r["result"] for k in ("analyse","xlsx_base64")):
    ok = False; print("FEJL: salgsanalyse-demo ikke IP-sikker")

# konkurrentanalyse via router (struktureret input)
r = route({"type": "konkurrentanalyse",
           "own": {"name":"a","avg_price":250,"product_count":100,"traffic_estimate":5000,"ai_visibility":20,"shipping_free_over":299},
           "competitors":[{"name":"b","avg_price":200,"product_count":300,"traffic_estimate":20000,"ai_visibility":60,"shipping_free_over":499}]})
if not r["ok"] or "where_to_win" not in r["result"]:
    ok = False; print("FEJL: konkurrentanalyse-routing")

# landingsside via router
r = route({"type": "landingsside", "page_text": "# Køb nu\n\nBedst i test. Kontakt tlf 123. [Køb]"})
if not r["ok"] or "score" not in r["result"]:
    ok = False; print("FEJL: landingsside-routing")

# fejl-input (tom CSV) håndteres
r = route({"type": "produkttekst", "csv": "ingen;kolonner\n"})
if r["ok"] is not False:
    ok = False; print("FEJL: dårligt input burde give ok=False")

print("Router dækker", len(REGISTRY), "produkttyper.")
print("RESULTAT:", "✓ OK" if ok else "✗ FEJL")
print("Live Vertex-forklaring aktiveres med GEMINI_ENABLED=1 ved deploy (ikke testet mod live).")
