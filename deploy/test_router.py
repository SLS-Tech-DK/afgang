"""Test af Cloud Function-routeren: rigtige typer ruter til rigtige motorer,
ukendt type fejler pænt, deterministisk resultat kommer igennem."""
import io, csv
from main import route, REGISTRY

ok = True

# alle typer er registreret
expected = {"salgsanalyse","indkobsanalyse","lageranalyse","kundeanalyse","butiksanalyse",
            "konkurrentanalyse","ai_synlighed","prisovervagning","naevner_ai_alarm",
            "produkttekst","review_analyse","landingsside","annonce_spild","soegeords_gap"}
if set(REGISTRY) != expected:
    ok = False; print("FEJL: registry mangler typer:", expected ^ set(REGISTRY))

# ukendt type
r = route({"type": "findes_ikke"})
if r["ok"] or "Ukendt type" not in r["error"]:
    ok = False; print("FEJL: ukendt type burde fejle pænt")

# salgsanalyse via router
buf = io.StringIO(); csv.writer(buf).writerows(
    [["Order ID","Lineitem name","Lineitem quantity","Lineitem price"],
     ["1","Kaffe","2","79.50"],["1","Filter","1","29.00"],["2","Kaffe","1","79.50"]])
r = route({"type": "salgsanalyse", "csv": buf.getvalue()})
if not r["ok"] or r["type"] != "salgsanalyse" or "bestsellers" not in r["result"]:
    ok = False; print("FEJL: salgsanalyse-routing")

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
