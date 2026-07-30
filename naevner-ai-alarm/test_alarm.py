"""Test af 'Nævner AI min virksomhed'-alarm: baseline, ændringsalarm, konkurrent-fremgang."""
from naevner_ai_alarm import run_check, compare
from ai_synlighed import geo_visibility

brand = "MinShop"
comps = ["KonkA", "KonkB"]

# Måned 1 (baseline): brand nævnt 1 af 4
qr1 = [
    {"query": "q1", "response": "KonkA er bedst."},
    {"query": "q2", "response": "MinShop og KonkA."},
    {"query": "q3", "response": "KonkA, KonkB."},
    {"query": "q4", "response": "KonkB leverer hurtigt."},
]
r1 = run_check(qr1, brand, comps, previous_measurement=None)
print("Måned 1 alarm:", r1["comparison"]["alarm"], "| alerts:", [a["type"] for a in r1["comparison"]["alerts"]])

ok = True
# baseline: ingen ægte alarm, kun baseline-besked
if r1["comparison"]["alarm"] is not False:
    ok = False; print("FEJL: baseline burde ikke give alarm=True")
if r1["comparison"]["alerts"][0]["type"] != "baseline":
    ok = False; print("FEJL: første måling burde være baseline")

# Måned 2: brand nævnt 3 af 4 (stor stigning) → mention_rate op
qr2 = [
    {"query": "q1", "response": "MinShop er bedst."},
    {"query": "q2", "response": "MinShop og KonkA."},
    {"query": "q3", "response": "MinShop, KonkB."},
    {"query": "q4", "response": "KonkB leverer hurtigt."},
]
r2 = run_check(qr2, brand, comps, previous_measurement=r1["measurement"])
print("Måned 2 deltas:", r2["comparison"]["deltas"])
print("Måned 2 alerts:", [(a["type"], a.get("direction")) for a in r2["comparison"]["alerts"]])

# måned1 rate = 1/4=25%, måned2 = 3/4=75% → +50pp
if r2["comparison"]["deltas"]["mention_rate_delta_pp"] != 50.0:
    ok = False; print("FEJL: mention-rate delta burde være +50pp")
if not r2["comparison"]["alarm"]:
    ok = False; print("FEJL: stor ændring burde give alarm")
rate_alert = [a for a in r2["comparison"]["alerts"] if a["type"] == "mention_rate"]
if not rate_alert or rate_alert[0]["direction"] != "op":
    ok = False; print("FEJL: mention_rate-alarm burde være 'op'")

# Måned 3: konkurrent rykker frem (KonkA nævnt mere, brand falder)
qr3 = [
    {"query": "q1", "response": "KonkA."},
    {"query": "q2", "response": "KonkA."},
    {"query": "q3", "response": "KonkA."},
    {"query": "q4", "response": "MinShop."},
]
r3 = run_check(qr3, brand, comps, previous_measurement=r2["measurement"])
types3 = [a["type"] for a in r3["comparison"]["alerts"]]
print("Måned 3 alerts:", types3)
if "competitor_gain" not in types3:
    ok = False; print("FEJL: KonkA-fremgang burde give competitor_gain-alarm")
if "mention_rate" not in types3:
    ok = False; print("FEJL: fald i mention-rate burde alarmere")

print("\nRESULTAT:", "✓ OK" if ok else "✗ FEJL")
print("Live model-forespørgsler IKKE testet — wires ved deployment.")
