"""Tests: de to nye Gemini-lag (mock) + premium samle-motoren."""
import io, csv
from datetime import date, timedelta

# --- byg datasæt med kunde + dato + flere produkter ---
start = date(2026, 1, 1)
rows = [["Ordrenr", "Varenavn", "Antal", "Beløb", "Ordredato", "Kunde"]]
oid = 0
def add(prod, qty, amt, day, cust):
    global oid; oid += 1
    rows.append([oid, prod, qty, f"{amt},00", (start+timedelta(days=day)).strftime("%d-%m-%Y"), cust])
for wk in range(20):
    add("Kaffe", 2, 160, wk*7, f"K{wk%5}")
    if wk < 15: add("Filter", 1, 29, wk*7, f"K{wk%5}")
for d in [10, 40]:
    add("Vin", 1, 120, d, f"V{d}")
buf = io.StringIO(); csv.writer(buf, delimiter=";").writerows(rows)
data = buf.getvalue()
stock = "Produkt;Lagerantal;Kostpris\nKaffe;50;40,00\nFilter;200;10,00\nVin;80;60,00\n"

ok = True

# 1) Lager Gemini-lag (mock)
import lageranalyse, lager_forklaring
la = lageranalyse.analyze(data, stock_csv_text=stock)
cap = {}
lr = lager_forklaring.forklar(la, caller=lambda s,p: (cap.update({"p":p}), "MOCK")[1])
if "DØDVARER" not in cap["p"] or "forklaring_tekst" not in lr:
    ok = False; print("FEJL: lager_forklaring")

# 2) Kunde Gemini-lag (mock)
import kundeanalyse, kunde_forklaring
ka = kundeanalyse.analyze(data)
cap2 = {}
kr = kunde_forklaring.forklar(ka, caller=lambda s,p: (cap2.update({"p":p}), "MOCK")[1])
if "TOP KUNDER" not in cap2["p"] or "forklaring_tekst" not in kr:
    ok = False; print("FEJL: kunde_forklaring")

# 3) Premium samle-motor
import butiksanalyse
full = butiksanalyse.analyze(data, stock_csv_text=stock)
for sec in ("salgsanalyse", "indkobsanalyse", "lageranalyse", "kundeanalyse", "kryds", "handlingsplan"):
    if sec not in full:
        ok = False; print("FEJL: premium mangler sektion", sec)
# margin på tværs skal give tal når stock+cost er der; Kaffe: rev=20*160=3200, cogs=40*40=1600, margin=1600
marg = full["kryds"]["margin_paa_tvaers"].get("by_product", [])
kaffe = [m for m in marg if m["product"] == "Kaffe"]
if not kaffe or abs(kaffe[0]["gross_margin"] - 1600) > 0.01:
    ok = False; print("FEJL: margin på tværs forkert:", kaffe)
if not full["handlingsplan"]:
    ok = False; print("FEJL: tom handlingsplan")
print("Handlingsplan:")
for p in full["handlingsplan"]:
    print("  -", p)
print("Margin top:", [(m["product"], m["gross_margin"], m["margin_pct"]) for m in marg])

print("\nRESULTAT:", "✓ OK" if ok else "✗ FEJL")
print("Live Vertex-kald IKKE testet — kræver nøgle ved deployment.")
