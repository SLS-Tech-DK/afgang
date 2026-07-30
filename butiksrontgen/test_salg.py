"""Test af salgsanalyse-motoren mod syntetiske data i to CSV-formater.
Verificerer at tal er korrekte og at kolonne-genkendelse virker på begge."""
import io, csv, random, json
from salgsanalyse import analyze, load_lines

random.seed(42)

# --- Byg en KONTROLLERET datasæt med kendte mønstre ---------------------------
# Produkter: Kaffe, Filter, Kop, Kande, The
# Plantet mønster:
#   - Kaffe er bestseller (høj volumen)
#   - Kaffe+Filter købes næsten altid sammen (bundle-kandidat)
#   - Kaffe og The købes stort set ALDRIG sammen (kannibaliserings-signal)
orders = []
oid = 0
def add(order_id, product, qty, unit):
    orders.append((order_id, product, qty, unit))

# 60 kaffe-ordrer, hvoraf 50 også har filter
for i in range(60):
    oid += 1
    add(oid, "Kaffe", 2, 79.50)
    if i < 50:
        add(oid, "Filter", 1, 29.00)
    if i < 15:
        add(oid, "Kop", 1, 49.00)

# 40 the-ordrer, aldrig sammen med kaffe
for i in range(40):
    oid += 1
    add(oid, "The", 1, 59.00)
    if i < 10:
        add(oid, "Kande", 1, 199.00)

# beregn forventede værdier uafhængigt
exp_kaffe_rev = 60 * 2 * 79.50
exp_filter_rev = 50 * 1 * 29.00
exp_the_rev = 40 * 1 * 59.00
exp_total = exp_kaffe_rev + exp_filter_rev + 15*49.00 + exp_the_rev + 10*199.00

# --- Format A: Shopify-agtig, engelske headers, komma-separeret ----------------
buf = io.StringIO()
w = csv.writer(buf)
w.writerow(["Order ID", "Lineitem name", "Lineitem quantity", "Lineitem price", "Created at", "Email"])
for o, p, q, u in orders:
    w.writerow([f"#{1000+o}", p, q, f"{u:.2f}", "2026-06-15", f"kunde{o}@mail.dk"])
csv_a = buf.getvalue()

# --- Format B: dansk, semikolon, komma-decimal, andre kolonnenavne ------------
buf = io.StringIO()
w = csv.writer(buf, delimiter=";")
w.writerow(["Ordrenr", "Varenavn", "Antal", "Beløb", "Ordredato", "Kunde"])
for o, p, q, u in orders:
    w.writerow([o, p, q, f"{u*q:.2f}".replace(".", ","), "15-06-2026", f"K{o}"])
csv_b = buf.getvalue()

def check(name, csv_text):
    print(f"\n===== {name} =====")
    lines, mapping = load_lines(csv_text)
    print("Kolonne-mapping:", mapping)
    res = analyze(csv_text)
    m = res["meta"]
    print("Total omsætning:", m["total_revenue"], "| forventet:", round(exp_total, 2))
    top = res["bestsellers"]["by_revenue"][0]
    print("Bestseller:", top["product"], top["revenue"])
    print("Top købes-sammen:", res["co_purchase"][0] if res["co_purchase"] else None)
    print("Bundles:", [b["products"] for b in res["bundles"]])
    print("Kannibalisering:", [c["products"] for c in res["cannibalization"]])

    ok = True
    if top["product"] != "Kaffe":
        ok = False; print("FEJL: bestseller burde være Kaffe")
    if abs(m["total_revenue"] - round(exp_total, 2)) > 1.0:
        ok = False; print("FEJL: total omsætning matcher ikke")
    pairs = [set(b["products"]) for b in res["bundles"]]
    if {"Kaffe", "Filter"} not in pairs:
        ok = False; print("FEJL: Kaffe+Filter burde være bundle-forslag")
    cann = [set(c["products"]) for c in res["cannibalization"]]
    if {"Kaffe", "The"} not in cann:
        ok = False; print("FEJL: Kaffe+The burde være kannibaliserings-signal")
    print("RESULTAT:", "✓ OK" if ok else "✗ FEJL")
    return ok

a = check("Format A (Shopify, engelsk, komma)", csv_a)
b = check("Format B (dansk, semikolon, komma-decimal)", csv_b)
print("\n=== SAMLET:", "ALLE OK ✓" if a and b else "FEJL ✗", "===")
