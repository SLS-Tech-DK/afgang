"""Tests for kundeanalyse: CLV, churn, segments, RFM — mod syntetisk data med kendt facit."""
import sys, kundeanalyse
ok=True
def chk(c,m):
    global ok
    if not c: ok=False; print("FEJL:",m)

# 3 kunder: A køber tit+nyligt+meget (champion), B engangs gammel (tabt), C middel
rows=["Ordrenr,Varenavn,Antal,Beloeb,Ordredato,Kunde"]
for i in range(6): rows.append(f"A{i},Kaffe,1,200,2026-06-2{i},a@x.dk")   # 6 ordrer, nyligt, 1200
rows.append("B1,Kaffe,1,100,2026-01-01,b@x.dk")                            # 1 ordre, gammelt
for i in range(2): rows.append(f"C{i},Kaffe,1,150,2026-05-1{i},c@x.dk")   # 2 ordrer, middel
csv="\n".join(rows)
r=kundeanalyse.analyze(csv)
chk(r["meta"]["distinct_customers"]==3, "3 kunder")
top=r["clv"][0]
chk(top["customer"]=="a@x.dk" and top["orders"]==6, "CLV-top er a med 6 ordrer")
seg=r["segments"]
chk(seg["repeat_customers"]==2 and seg["one_time_customers"]==1, "segments: 2 gengangere, 1 engangs")
# RFM
rfm=r["rfm_segments"]["by_segment"]
names={s["segment"] for s in rfm}
total_cust=sum(s["customers"] for s in rfm)
chk(total_cust==3, "RFM dækker alle 3 kunder")
chk(len(rfm)>=1, "RFM giver segmenter")
# churn: b er gammel -> med i churn_signal (>120 dage fra ref 2026-06-25)
chk(any(c["customer"]=="b@x.dk" for c in r["churn_signal"]), "b er churn-signal")

# manglende kunde-kolonne -> pæn fejl
chk("error" in kundeanalyse.analyze("Varenavn,Antal,Beloeb\nKaffe,1,100"), "ingen kunde-kolonne -> fejl")

print("RESULTAT:", "OK" if ok else "FEJL")
sys.exit(0 if ok else 1)
