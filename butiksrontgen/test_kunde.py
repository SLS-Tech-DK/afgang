"""Test af Kundeanalyse mod kontrolleret datasæt.
Kunde 'Storkunde': mange køb, høj omsætning (top CLV, gengangere).
Kunde 'Engangs': ét køb tidligt (churn-signal).
Kunde 'Loyal': flere køb, seneste nyligt."""
import io, csv
from datetime import date, timedelta
from kundeanalyse import analyze

start = date(2026, 1, 1)
rows = [["Ordrenr", "Varenavn", "Beløb", "Ordredato", "Kunde"]]
oid = 0
def add(prod, amt, day, cust):
    global oid; oid += 1
    rows.append([oid, prod, f"{amt},00", (start+timedelta(days=day)).strftime("%d-%m-%Y"), cust])

# Storkunde: 5 ordrer, høj værdi, seneste dag 200
for i, d in enumerate([10, 50, 100, 150, 200]):
    add("Vare", 1000, d, "Storkunde")
# Loyal: 3 ordrer, seneste dag 205
for d in [30, 120, 205]:
    add("Vare", 200, d, "Loyal")
# Engangs: 1 ordre dag 5 (churn — 200 dage siden ift. ref 205)
add("Vare", 300, 5, "Engangs")

buf = io.StringIO(); csv.writer(buf, delimiter=";").writerows(rows)
res = analyze(buf.getvalue(), churn_days=120)

print("Ref:", res["meta"]["reference_date"], "| kunder:", res["meta"]["distinct_customers"])
print("Top CLV:", [(c["customer"], c["revenue"], c["orders"]) for c in res["clv"]])
print("Churn:", [(c["customer"], c["days_since"]) for c in res["churn_signal"]])
print("Segmenter:", res["segments"])

ok = True
if res["clv"][0]["customer"] != "Storkunde":
    ok = False; print("FEJL: Storkunde burde have højest CLV")
if res["clv"][0]["revenue"] != 5000:
    ok = False; print("FEJL: Storkunde omsætning burde være 5000")
churn = [c["customer"] for c in res["churn_signal"]]
if "Engangs" not in churn:
    ok = False; print("FEJL: Engangs burde være churn-signal")
if "Loyal" in churn or "Storkunde" in churn:
    ok = False; print("FEJL: aktive kunder burde ikke være churn")
seg = res["segments"]
if seg["repeat_customers"] != 2 or seg["one_time_customers"] != 1:
    ok = False; print("FEJL: segment-optælling forkert")
# manglende kunde-kolonne → fejl
no_cust = analyze("Vare;Beløb\nÆble;10\n")
if "error" not in no_cust:
    ok = False; print("FEJL: manglende kunde-kolonne burde give fejl")
print("\nRESULTAT:", "✓ OK" if ok else "✗ FEJL")
