"""Test af Indkøbsanalyse mod kontrolleret datasæt med KENDTE mønstre.
Mælk: højfrekvent, kunde genkøber hver 7. dag. Vin: sjælden.
Verificerer hastigheds-rangering og genkøbsinterval."""
import io, csv
from datetime import date, timedelta
from indkobsanalyse import analyze

start = date(2026, 1, 1)
rows = [["Ordrenr", "Varenavn", "Antal", "Beløb", "Ordredato", "Kunde"]]
oid = 0
# Mælk: kunde A køber hver 7. dag i 10 uger (=10 køb, 9 intervaller à 7 dage), 2 stk pr gang
for wk in range(10):
    oid += 1
    d = (start + timedelta(days=wk*7)).strftime("%d-%m-%Y")
    rows.append([oid, "Mælk", 2, "20,00", d, "A"])
# Mælk: kunde B køber hver 7. dag i 6 uger
for wk in range(6):
    oid += 1
    d = (start + timedelta(days=wk*7)).strftime("%d-%m-%Y")
    rows.append([oid, "Mælk", 1, "10,00", d, "B"])
# Vin: sjældent, 3 køb spredt, forskellige kunder (intet genkøbsmønster)
for i, day in enumerate([5, 40, 68]):
    oid += 1
    d = (start + timedelta(days=day)).strftime("%d-%m-%Y")
    rows.append([oid, "Vin", 1, "120,00", d, f"V{i}"])

buf = io.StringIO(); csv.writer(buf, delimiter=";").writerows(rows)
res = analyze(buf.getvalue())

print("Span dage:", res["meta"]["span_days"], "| advarsler:", res["meta"]["warnings"])
print("Hastighed (top):", [(v["product"], v["units_per_day"]) for v in res["velocity"]])
print("Genkøbsinterval:", res["repurchase_intervals"])
print("Genbestillingsliste:", [(r["product"], r["suggested_reorder_cadence_days"]) for r in res["reorder_list"]])

ok = True
# Mælk skal være hurtigst
if res["velocity"][0]["product"] != "Mælk":
    ok = False; print("FEJL: Mælk burde have højest hastighed")
# Genkøbsinterval for Mælk skal være ~7 dage
milk = [i for i in res["repurchase_intervals"] if i["product"] == "Mælk"]
if not milk or abs(milk[0]["avg_days_between_repurchase"] - 7.0) > 0.01:
    ok = False; print("FEJL: Mælk genkøbsinterval burde være 7.0")
# Vin har intet genkøbsmønster (ingen kunde køber to gange)
if any(i["product"] == "Vin" for i in res["repurchase_intervals"]):
    ok = False; print("FEJL: Vin burde ikke have genkøbsinterval")
# hastighed korrekt: Mælk units = 10*2 + 6*1 = 26; span = 9*7+1 = 64 dage
span = res["meta"]["span_days"]
exp_v = round(26 / span, 3)
got_v = res["velocity"][0]["units_per_day"]
if abs(got_v - exp_v) > 0.001:
    ok = False; print(f"FEJL: Mælk hastighed {got_v} != forventet {exp_v}")

print("\nRESULTAT:", "✓ OK" if ok else "✗ FEJL")
