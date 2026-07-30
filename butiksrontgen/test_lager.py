"""Test af Lageranalyse mod kontrolleret datasæt.
Kendt: 'Solcreme' solgt kun i sommer og aldrig senere = dødvare + sæson.
'Brød' solgt jævnt. Plus valgfri lager-CSV til kapitalbinding."""
import io, csv
from datetime import date, timedelta
from lageranalyse import analyze

start = date(2026, 1, 1)
rows = [["Ordrenr", "Varenavn", "Antal", "Beløb", "Ordredato"]]
oid = 0
# Brød: sælges hver uge hele året
for wk in range(30):
    oid += 1
    rows.append([oid, "Brød", 5, "50,00", (start+timedelta(days=wk*7)).strftime("%d-%m-%Y")])
# Solcreme: kun juni-juli (dag 150-210), intet efter → dødvare ift. seneste dato
for d in [155, 160, 175, 200]:
    oid += 1
    rows.append([oid, "Solcreme", 2, "80,00", (start+timedelta(days=d)).strftime("%d-%m-%Y")])

buf = io.StringIO(); csv.writer(buf, delimiter=";").writerows(rows)
# seneste salg er Brød omkring dag 203; Solcreme sidst dag 200 → ikke dødvare hvis <90 dage
# gør Brød løber til dag 203, ref=203; Solcreme sidst 200 → 3 dage siden, IKKE dødvare
res = analyze(buf.getvalue(), deadstock_days=90)
print("Ref dato:", res["meta"]["reference_date"])
print("Dødvarer (90d):", [(d["product"], d["days_since"]) for d in res["deadstock"]])
print("Langsomst:", [(s["product"], s["units_per_day"]) for s in res["slow_movers"]])
print("Sæson (måneder):", [m["month"] for m in res["seasonality"]])
print("Kapitalbinding uden lager-CSV:", "note" in res["capital_tied"])

# Test med kort dødvare-vindue så Solcreme fanges (30 dage: intet solgt siden dag 200, men Brød kører til 203)
res2 = analyze(buf.getvalue(), deadstock_days=1)
dead2 = [d["product"] for d in res2["deadstock"]]

# Lager-CSV til kapitalbinding
stock = "Produkt;Lagerantal;Kostpris\nSolcreme;100;40,00\nBrød;5;10,00\n"
cap = analyze(buf.getvalue(), stock_csv_text=stock)["capital_tied"]
print("Kapitalbinding total:", cap.get("total_capital_tied"), "| top:", cap["by_product"][0] if "by_product" in cap else cap)

ok = True
if res["slow_movers"][0]["product"] != "Solcreme":
    ok = False; print("FEJL: Solcreme burde være langsomst (færrest enheder/dag)")
if "note" not in res["capital_tied"]:
    ok = False; print("FEJL: uden lager-CSV skal kapitalbinding give note")
# kapitalbinding: Solcreme 100*40=4000, Brød 5*10=50, total 4050, top Solcreme
if abs(cap["total_capital_tied"] - 4050) > 0.01:
    ok = False; print("FEJL: kapitalbinding total forkert")
if cap["by_product"][0]["product"] != "Solcreme":
    ok = False; print("FEJL: Solcreme burde binde mest kapital")
if len(res["seasonality"]) < 2:
    ok = False; print("FEJL: sæson burde have flere måneder")
print("\nRESULTAT:", "✓ OK" if ok else "✗ FEJL")
