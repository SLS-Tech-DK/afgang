"""Test af Prisovervågning: prisposition, ændringsdetektion, fetcher-mock."""
from prisovervagning import analyze, price_position, detect_changes, collect_snapshot

# nuværende snapshot
current = [
    {"product": "Kaffe", "own": 79, "competitors": {"KonkA": 75, "KonkB": 85}},
    {"product": "The", "own": 59, "competitors": {"KonkA": 65, "KonkB": 62}},
    {"product": "Kande", "own": 199, "competitors": {"KonkA": 150, "KonkB": 160}},
]
# forrige snapshot (KonkA sænkede Kaffe fra 90→75; KonkB hævede The 60→62)
previous = [
    {"product": "Kaffe", "own": 79, "competitors": {"KonkA": 90, "KonkB": 85}},
    {"product": "The", "own": 59, "competitors": {"KonkA": 65, "KonkB": 60}},
    {"product": "Kande", "own": 199, "competitors": {"KonkA": 150, "KonkB": 160}},
]
res = analyze(current, previous, threshold_pct=1.0)

pos = {p["product"]: p for p in res["positions"]}
print("Kaffe position:", pos["Kaffe"].get("position"))
print("The position:", pos["The"].get("position"))
print("Kande position:", pos["Kande"].get("position"))
print("Alarmer:")
for a in res["alerts"]:
    print(" ", a["competitor"], a["product"], a["old_price"], "->", a["new_price"], f"({a['change_pct']}% {a['direction']})")

ok = True
# Kaffe: own 79, comps 75/85 → midt
if pos["Kaffe"]["position"] != "midt":
    ok = False; print("FEJL: Kaffe burde være midt")
# The: own 59, comps 65/62 → billigst
if pos["The"]["position"] != "billigst":
    ok = False; print("FEJL: The burde være billigst")
# Kande: own 199, comps 150/160 → dyrest
if pos["Kande"]["position"] != "dyrest":
    ok = False; print("FEJL: Kande burde være dyrest")
# alarmer: KonkA Kaffe 90->75 = -16.7%, KonkB The 60->62 = +3.3%
kaffe_alert = [a for a in res["alerts"] if a["product"] == "Kaffe" and a["competitor"] == "KonkA"]
if not kaffe_alert or kaffe_alert[0]["direction"] != "ned" or abs(kaffe_alert[0]["change_pct"] + 16.7) > 0.2:
    ok = False; print("FEJL: Kaffe/KonkA-alarm forkert:", kaffe_alert)
the_alert = [a for a in res["alerts"] if a["product"] == "The" and a["competitor"] == "KonkB"]
if not the_alert or the_alert[0]["direction"] != "op":
    ok = False; print("FEJL: The/KonkB-alarm forkert")
# største ændring skal ligge først
if res["alerts"][0]["product"] != "Kaffe":
    ok = False; print("FEJL: største ændring burde være øverst")
# uændrede (Kande) må ikke give alarm
if any(a["product"] == "Kande" for a in res["alerts"]):
    ok = False; print("FEJL: uændret pris gav alarm")

# fetcher-mock
prices = {"u_kaffe": 79.0, "u_kaffe_a": 75.0}
snap = collect_snapshot(["Kaffe"], {"Kaffe": "u_kaffe"}, {"KonkA": {"Kaffe": "u_kaffe_a"}},
                        fetcher=lambda u: prices[u])
if snap[0]["own"] != 79.0 or snap[0]["competitors"]["KonkA"] != 75.0:
    ok = False; print("FEJL: collect_snapshot mock")

print("\nRESULTAT:", "✓ OK" if ok else "✗ FEJL")
print("Live scraping IKKE testet — wires ved deployment.")
