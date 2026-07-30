"""Test af Konkurrentanalyse-kernen mod kontrolleret input + mock-fetcher + Gemini-mock."""
from konkurrentanalyse import analyze, collect, where_to_win
from konk_forklaring import forklar, SYSTEM_INSTRUKTION

# Kontrolleret: egen shop er dyrere, smallere sortiment, mindre trafik, lav AI-synlighed,
# men har lavere fri fragt-grænse (bedre). Konkurrenter er billigere/større.
own = {"name": "minshop.dk", "avg_price": 250, "product_count": 100,
       "traffic_estimate": 5000, "ai_visibility": 20, "shipping_free_over": 299}
comps = [
    {"name": "konkA.dk", "avg_price": 200, "product_count": 300,
     "traffic_estimate": 20000, "ai_visibility": 60, "shipping_free_over": 499},
    {"name": "konkB.dk", "avg_price": 220, "product_count": 250,
     "traffic_estimate": 15000, "ai_visibility": 45, "shipping_free_over": 399},
]
res = analyze(own, comps)
print("Gaps:")
for g in res["gaps"]:
    print(" ", g["field"], g["status"], "gap", g["gap"])
print("Hvor vinde:", [(w["field"], w["gap"]) for w in res["where_to_win"]])

ok = True
gapmap = {g["field"]: g for g in res["gaps"]}
# egen er bagud på: product_count, traffic, ai_visibility, avg_price (dyrere)
for f in ["product_count", "traffic_estimate", "ai_visibility", "avg_price"]:
    if gapmap[f]["status"] != "bagud":
        ok = False; print(f"FEJL: {f} burde være bagud")
# egen er FORAN på shipping_free_over (lavere grænse = bedre)
if gapmap["shipping_free_over"]["status"] != "foran":
    ok = False; print("FEJL: shipping_free_over burde være foran")
# where_to_win må kun indeholde bagud-felter
wf = {w["field"] for w in res["where_to_win"]}
if "shipping_free_over" in wf:
    ok = False; print("FEJL: foran-felt burde ikke være i where_to_win")
# traffic har størst relativ gap (15000/20000=0.75) → burde ligge højt
if res["where_to_win"][0]["field"] not in ("traffic_estimate", "ai_visibility", "product_count"):
    ok = False; print("FEJL: forventede stort-gap-felt øverst")

# collect med mock-fetcher
def mock_fetch(domain):
    return {"avg_price": 100, "product_count": 10, "traffic_estimate": 1000,
            "ai_visibility": 10, "shipping_free_over": 199}
o, c = collect("minshop.dk", ["a.dk", "b.dk"], fetcher=mock_fetch)
if o["name"] != "minshop.dk" or len(c) != 2:
    ok = False; print("FEJL: collect mock")

# Gemini-lag mock
cap = {}
fr = forklar(res, caller=lambda s, p: (cap.update({"s": s, "p": p}), "MOCK")[1])
if cap["s"] != SYSTEM_INSTRUKTION or "SIDE-OM-SIDE" not in cap["p"] or "forklaring_tekst" not in fr:
    ok = False; print("FEJL: konk_forklaring")

print("\nRESULTAT:", "✓ OK" if ok else "✗ FEJL")
print("Live fetch + live Vertex-kald IKKE testet — wires ved deployment.")
