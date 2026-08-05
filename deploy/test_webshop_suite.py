"""Tests for den generaliserede webshop-suite: tre formater + degradering."""
import sys, webshop_suite as ws
ok=True
def chk(c,m):
    global ok
    if not c: ok=False; print("FEJL:",m)

# 1) ideal.shop-stil (embedded linjer, dansk, semikolon)
vare="Varenummer;Navn;Primær kategori;Mærke;Pris;Indkøbspris;Lager\n1;Kaffe;Kaffe;A;100;60;40\n2;Filter;Tilbehør;B;30;10;200"
ordre=("Ordrenr;Produkt varenumre;Produkt titler;Ordredato;Kunde postnr.;Kunde firma;Fragtmetode\n"
       "1;1|||2;Kaffe (2)|||Filter (1);01-03-2026;9300;;Afhentning\n"
       "2;1;Kaffe (1);02-03-2026;2100;Firma ApS;Levering")
r=ws.analyze(vare,ordre); m=r["meta"]
chk(m["ordre_mode"]=="embedded","mode embedded")
chk(m["omsætning"]==100*3+30, "oms embedded")           # 2*100+1*30 +1*100 = 330
chk(m["kan"]["margin"] and m["kan"]["geografi"] and m["kan"]["b2b"], "capabilities embedded")
chk(r["levering"]["afhentning"]==1, "afhentning fanget")

# 2) Shopify-stil (per-linje, engelsk, komma)
v2="Title,Vendor,Type,Variant SKU,Variant Price,Cost per item,Variant Inventory Qty\nKaffe,A,Kaffe,S1,99,55,40\nKande,A,Udstyr,S2,299,180,8"
o2=("Name,Created at,Lineitem quantity,Lineitem name,Lineitem sku,Billing Zip,Shipping Method\n"
    "#1,2026-03-01 10:00:00,2,Kaffe,S1,2100,Standard\n#2,2026-03-02 14:00:00,1,Kande,S2,8000,Pickup")
r2=ws.analyze(v2,o2); m2=r2["meta"]
chk(m2["ordre_mode"]=="perline","mode perline")
chk(m2["omsætning"]==2*99+299,"oms perline")            # 497
chk(m2["kan"]["margin"],"margin perline")
chk(r2["levering"]["afhentning"]==1,"pickup engelsk fanget")

# 3) minimal data → degradering
v3="Varenummer;Navn;Pris\n1;Kaffe;99"
o3="Ordrenr;Produkt varenumre;Produkt titler\n1;1;Kaffe (2)"
m3=ws.analyze(v3,o3)["meta"]
chk(m3["omsætning"]==198,"oms minimal")
chk(not m3["kan"]["margin"] and not m3["kan"]["geografi"],"degraderer uden margin/geo")

# 4) tomt ordre → pæn fejl
chk("error" in ws.analyze("Varenummer;Navn\n1;X","Ordrenr\n"),"tom ordre -> pæn fejl")

print("RESULTAT:", "OK" if ok else "FEJL")
sys.exit(0 if ok else 1)

# 5) render + qa (mock) — bygger på embedded-datasæt fra test 1
def _extra():
    va="Varenummer;Navn;Primær kategori;Mærke;Pris;Indkøbspris;Lager\n1;Kaffe;Kaffe;A;100;60;40\n2;Filter;Tilbehør;B;30;10;200"
    od=("Ordrenr;Produkt varenumre;Produkt titler;Ordredato;Kunde postnr.;Fragtmetode\n"
        "1;1|||2;Kaffe (2)|||Filter (1);01-03-2026;9300;Afhentning\n2;1;Kaffe (1);02-03-2026;2100;Levering")
    an=ws.analyze(va,od)
    h=ws.render_html(an,"Test"); chk("<canvas" in h and "Fejl" not in h[:200],"render_html producerer grafer")
    import io as _io, openpyxl
    xb=ws.render_xlsx(an); wb=openpyxl.load_workbook(_io.BytesIO(xb))
    chk("Indkobsordre" in wb.sheetnames and "Raadata" in wb.sheetnames,"render_xlsx har interaktive faner")
    q=ws.gemini_qa(an,"bedste kategori?",caller=lambda s,p:"Kaffe" if "kategori" in p.lower() else "?")
    chk(q["svar"]=="Kaffe","gemini_qa svarer via mock")
_extra()
print("RESULTAT2:", "OK" if ok else "FEJL"); sys.exit(0 if ok else 1)
