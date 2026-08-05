"""
SLS Tech · Afgang — Webshop-suite (generaliseret butiksanalyse-motor).
Tager TO udtræk fra en vilkårlig webshop: vareudtræk (katalog) + ordreudtræk (salg).
Fleksibel kolonne-genkendelse (dansk + engelsk + Shopify/WooCommerce). Degradér
pænt: mangler indkøbspris → ingen margin; mangler postnr → ingen geografi; osv.
Producerer én analyse-dict; render_html/render_xlsx ligger separat.
Ingen webshop hardkodet. Enerkeramik er kun brugt som testeksempel.
"""
from __future__ import annotations
import csv, io, re
from collections import defaultdict
from datetime import datetime
from itertools import combinations

def _rows(text):
    raw=text if isinstance(text,str) else text.decode("utf-8-sig","ignore")
    raw=raw.lstrip("﻿")
    sample=raw[:4000]
    delim=max([",",";","\t","|"], key=lambda d: sample.count(d))
    return list(csv.DictReader(io.StringIO(raw), delimiter=delim)), delim

def _norm(s): return re.sub(r"[^a-z0-9]","",(s or "").lower())

def _find(headers, pats):
    for h in headers:
        hn=_norm(h)
        for p in pats:
            if re.search(p,hn): return h
    return None

def _num(s):
    if s is None: return None
    s=str(s).strip()
    if s=="" : return None
    s=re.sub(r"[^0-9,.\-]","",s)
    if s.count(",") and s.count("."):
        if s.rfind(",")>s.rfind("."): s=s.replace(".","").replace(",",".")
        else: s=s.replace(",","")
    elif s.count(","):
        s=s.replace(".","").replace(",",".") if re.search(r",\d{1,2}$",s) else s.replace(",","")
    try: return float(s)
    except: return None

DATE_F=["%d-%m-%Y","%Y-%m-%d","%d/%m/%Y","%m/%d/%Y","%Y-%m-%dT%H:%M:%S","%d.%m.%Y","%Y/%m/%d","%d-%m-%Y %H:%M:%S","%Y-%m-%d %H:%M:%S"]
def _date(s):
    if not s: return None
    s=str(s).strip()
    for f in DATE_F:
        try: return datetime.strptime(s[:len(f)+2] if "%H" in f else s[:10], f.replace(" %H:%M:%S","") if "%H" not in f else f).date()
        except: pass
    m=re.search(r"(\d{4})[-/.](\d{1,2})[-/.](\d{1,2})", s) or re.search(r"(\d{1,2})[-/.](\d{1,2})[-/.](\d{4})", s)
    if m:
        g=list(map(int,m.groups()))
        try: return datetime(*(g if g[0]>31 else [g[2],g[1],g[0]])).date()
        except: return None
    return None
def _hour(s):
    m=re.search(r"(\d{1,2}):\d{2}", str(s or "")); return m.group(1).zfill(2) if m else ""

VARE_PATS=dict(
 vn=[r"varenummer",r"varenr",r"sku",r"artikel",r"^id$",r"itemnumber",r"produktid"],
 navn=[r"navn",r"titel",r"^name$",r"^title$",r"produktnavn",r"producttitle",r"varenavn"],
 kat=[r"prim.rkategori",r"kategori",r"category",r"producttype",r"^type$"],
 maerke=[r"m.rke",r"brand",r"vendor",r"producent",r"manufacturer"],
 pris=[r"^pris$",r"salgspris",r"^price$",r"variantprice",r"udsalgspris"],
 kost=[r"indk.{0,2}bspris",r"kostpris",r"^kost",r"^cost",r"costperitem",r"costprice",r"buyprice",r"indkobspris"],
 lager=[r"^lager$",r"beholdning",r"^stock",r"inventory",r"onhand",r"variantinventory",r"antalp.lager"],
)
def parse_vare(text):
    rows,_=_rows(text); heads=rows[0].keys() if rows else []
    heads=list(heads); mp={k:_find(heads,p) for k,p in VARE_PATS.items()}
    V={}
    for r in rows:
        vn=(r.get(mp["vn"]) or "").strip() if mp["vn"] else ""
        if not vn: continue
        V[vn]=dict(vn=vn,navn=(r.get(mp["navn"]) or vn).strip() if mp["navn"] else vn,
            kat=((r.get(mp["kat"]) or "Ukendt").strip() or "Ukendt") if mp["kat"] else "Ukendt",
            maerke=((r.get(mp["maerke"]) or "Ukendt").strip() or "Ukendt") if mp["maerke"] else "Ukendt",
            pris=_num(r.get(mp["pris"])) if mp["pris"] else None,
            kost=_num(r.get(mp["kost"])) if mp["kost"] else None,
            lager=(_num(r.get(mp["lager"])) or 0) if mp["lager"] else 0)
    return V, mp

ORD_PATS=dict(
 onr=[r"ordrenr",r"ordernumber",r"^order$",r"ordreid",r"^name$",r"ordre$",r"fakturanr"],
 dato=[r"ordredato",r"^dato$",r"^date$",r"createdat",r"created",r"fakturadato",r"orderdate"],
 tid=[r"ordretidspunkt",r"tidspunkt",r"^time$",r"createdat"],
 postnr=[r"kundepostnr",r"postnr",r"postnummer",r"^zip",r"postal",r"billingzip",r"shippingzip"],
 by=[r"kundeby",r"^by$",r"^city$",r"billingcity",r"shippingcity"],
 firma=[r"kundefirma",r"^firma$",r"company",r"billingcompany"],
 cvr=[r"cvr",r"vatnumber"],
 frag=[r"fragtmetode",r"leveringsmetode",r"shippingmethod",r"fulfillment",r"delivery"],
 betaling=[r"betalingsmetode",r"paymentmethod"],
 kunde=[r"kundenavn",r"kundeid",r"kundeemail",r"^email$",r"customer",r"billingname"],
 belob=[r"bel.bvarer",r"bel.btotal",r"subtotal",r"^total$",r"amount"],
 # embedded produktlinjer (ideal.shop)
 pvnums=[r"produktvarenumre",r"varenumre"],
 ptitler=[r"produkttitler",r"produkttitel"],
 # per-linje (Shopify-stil)
 li_sku=[r"lineitemsku",r"linjesku"],
 li_name=[r"lineitemname",r"linjenavn"],
 li_qty=[r"lineitemquantity",r"linjeantal",r"^antal$",r"quantity",r"stk"],
 li_product=[r"^produkt$",r"vare$",r"produktnavn"],
)
def parse_ordre(text, V):
    rows,_=_rows(text); heads=list(rows[0].keys()) if rows else []
    mp={k:_find(heads,p) for k,p in ORD_PATS.items()}
    lines=[]
    def base(r):
        return dict(onr=(r.get(mp["onr"]) or "").strip() if mp["onr"] else "",
            date=_date(r.get(mp["dato"])) if mp["dato"] else None,
            hour=_hour(r.get(mp["tid"]) or (r.get(mp["dato"]) if mp["dato"] else "")),
            postnr=(r.get(mp["postnr"]) or "").strip() if mp["postnr"] else "",
            by=(r.get(mp["by"]) or "").strip() if mp["by"] else "",
            b2b=bool(((r.get(mp["firma"]) or "").strip() if mp["firma"] else "") or ((r.get(mp["cvr"]) or "").strip() if mp["cvr"] else "")),
            firma=(r.get(mp["firma"]) or "").strip() if mp["firma"] else "",
            frag=(r.get(mp["frag"]) or "").strip() if mp["frag"] else "",
            kunde=(r.get(mp["kunde"]) or "").strip() if mp["kunde"] else "")
    def addline(b,vn,navn,qty):
        v=V.get(vn); pris=(v["pris"] if v else None) or 0; kost=(v["kost"] if v else None)
        lines.append(dict(**b, vn=vn, navn=(v["navn"] if v else (navn or vn)),
            kat=v["kat"] if v else "Ukendt", maerke=v["maerke"] if v else "Ukendt",
            qty=qty, rev=pris*qty, db=((pris-(kost or 0))*qty) if kost is not None else 0))
    mode="embedded" if mp["pvnums"] else ("perline" if (mp["li_sku"] or mp["li_name"] or mp["li_product"]) else "simple")
    synth=0
    for r in rows:
        b=base(r)
        if not b["onr"]: synth+=1; b["onr"]=f"_o{synth}"
        if mode=="embedded":
            vnums=(r.get(mp["pvnums"]) or "").split("|||"); tit=(r.get(mp["ptitler"]) or "").split("|||") if mp["ptitler"] else []
            for i,vn in enumerate(vnums):
                vn=vn.strip()
                if not vn: continue
                qty=1.0
                if i<len(tit):
                    m=re.search(r"\((\d+)\)\s*$", tit[i].strip()); qty=float(m.group(1)) if m else 1.0
                addline(b,vn,tit[i] if i<len(tit) else "",qty)
        else:
            vn=(r.get(mp["li_sku"]) or "").strip() if mp["li_sku"] else ""
            navn=(r.get(mp["li_name"]) or r.get(mp["li_product"]) or "").strip() if (mp["li_name"] or mp["li_product"]) else ""
            if not vn and navn:
                vn=navn  # fald tilbage til navn som nøgle
            if not vn: continue
            qty=(_num(r.get(mp["li_qty"])) if mp["li_qty"] else None) or 1.0
            addline(b,vn,navn,qty)
    return lines, mp, mode


def analyze(vare_csv, ordre_csv):
    V, vmap = parse_vare(vare_csv)
    lines, omap, mode = parse_ordre(ordre_csv, V)
    if not lines:
        return {"error":"Ingen ordrelinjer fundet — tjek ordreudtrækket.","vmap":vmap,"omap":omap}
    has_margin=any(v.get("kost") is not None for v in V.values()) and any(l["db"] for l in lines)
    has_geo=any(l["postnr"] for l in lines)
    has_time=any(l["date"] for l in lines)
    has_frag=any(l["frag"] for l in lines)
    has_b2b=any(l["b2b"] for l in lines)
    sold=defaultdict(float)
    for l in lines: sold[l["vn"]]+=l["qty"]
    O=defaultdict(lambda: dict(rev=0.0,kats=set(),frag="",omr="",b2b=False,kunde="",firma="",date=None,hour="",by=""))
    for l in lines:
        o=O[l["onr"]]; o["rev"]+=l["rev"]; o["kats"].add(l["kat"]); o["frag"]=l["frag"] or o["frag"]
        o["omr"]=(l["postnr"][:2]+"xx") if len(l["postnr"])>=2 else o["omr"]; o["b2b"]=o["b2b"] or l["b2b"]
        o["kunde"]=l["kunde"] or o["kunde"]; o["firma"]=l["firma"] or o["firma"]; o["date"]=l["date"] or o["date"]
        o["hour"]=l["hour"] or o["hour"]; o["by"]=l["by"] or o["by"]
    orders=list(O.values())
    oms=sum(l["rev"] for l in lines); db=sum(l["db"] for l in lines); nord=len(O); units=sum(l["qty"] for l in lines)
    def top(d,n=12): return sorted(d.items(),key=lambda x:-x[1])[:n]
    def A(k,v="rev"):
        d=defaultdict(float)
        for l in lines: d[l[k]]+=l[v]
        return d
    kr=A("kat"); kdb=A("kat","db"); kq=A("kat","qty"); mr=A("maerke"); mdb=A("maerke","db")
    prod_rev=A("navn"); prod_qty=A("navn","qty")
    pv=defaultdict(lambda:[0.0,0.0,0.0])
    for l in lines:
        a=pv[l["navn"]]; a[0]+=l["rev"]; a[1]+=l["db"]; a[2]+=l["qty"]
    thresh=sorted((r for r,_,_ in pv.values()),reverse=True)
    cut=thresh[min(len(thresh)-1,int(len(thresh)*0.2))] if thresh else 0
    prisjust=sorted([(n,d/r*100,r,q) for n,(r,d,q) in pv.items() if r>=cut and r>0],key=lambda x:x[1])[:15] if has_margin else []
    dates=[l["date"] for l in lines if l["date"]]; span_w=((max(dates)-min(dates)).days+1)/7 if dates else 52
    genbestil=[]; dodt=[]; lagervaerdi=0
    for vn,vv in V.items():
        s=sold.get(vn,0); lager=vv["lager"] or 0; vel=s/span_w if span_w else 0; lagervaerdi+=lager*(vv["kost"] or 0)
        if s>0 and vel>0 and lager/vel<4: genbestil.append((vv["navn"],round(vel,1),int(lager),round(lager/vel,1)))
        if lager>0 and s==0: dodt.append((vv["navn"],int(lager),round((vv["kost"] or 0)*lager)))
    genbestil.sort(key=lambda x:x[3]); dodt.sort(key=lambda x:-x[2]); dodt_total=sum(x[2] for x in dodt)
    omr_rev=defaultdict(float); omr_ord=defaultdict(int); omr_afh=defaultdict(int); omr_kat=defaultdict(lambda:defaultdict(float))
    for o in orders:
        if not o["omr"]: continue
        omr_rev[o["omr"]]+=o["rev"]; omr_ord[o["omr"]]+=1
        if o["frag"].lower().startswith(("afhent","pickup","pick up","hent")): omr_afh[o["omr"]]+=1
        for k in o["kats"]: omr_kat[o["omr"]][k]+=o["rev"]/max(1,len(o["kats"]))
    omr=top(omr_rev,10)
    byo=defaultdict(lambda:[0,0.0])
    for o in orders:
        if o["by"]: byo[o["by"]][0]+=1; byo[o["by"]][1]+=o["rev"]
    topbyer=sorted(byo.items(),key=lambda x:-x[1][0])[:15]
    afh=sum(1 for o in orders if o["frag"].lower().startswith(("afhent","pickup","pick up","hent"))); send=nord-afh
    hvad=[(a,[k for k,_ in sorted(omr_kat[a].items(),key=lambda x:-x[1])[:3]]) for a,_ in omr[:6]]
    kc=defaultdict(float); fc=defaultdict(float)
    for o in orders:
        kc[o["kunde"] or "—"]+=o["rev"]
        if o["firma"]: fc[o["firma"]]+=o["rev"]
    b2b=sum(o["rev"] for o in orders if o["b2b"]); priv=oms-b2b
    combo=defaultdict(int)
    for o in orders:
        for a,b in combinations(sorted(o["kats"]),2): combo[(a,b)]+=1
    DOWc=defaultdict(int); hourc=defaultdict(int); mnd=defaultdict(float)
    for o in orders:
        if o["date"]: DOWc[o["date"].weekday()]+=1
    for l in lines:
        if l["date"]: mnd[f"{l['date'].year}-{l['date'].month:02d}"]+=l["rev"]; hourc[int(l['hour']) if l['hour'].isdigit() else 0]+=0
    for o in orders:
        if o["hour"].isdigit(): hourc[int(o["hour"])]+=1
    return {
      "meta":{"omsætning":round(oms),"dækningsbidrag":round(db) if has_margin else None,
              "margin_pct":round(db/oms*100,1) if has_margin and oms else None,"ordrer":nord,"enheder":round(units),
              "gns_ordre":round(oms/nord) if nord else 0,"lagervaerdi":round(lagervaerdi),"dodt_total":dodt_total,
              "varer":len(V),"ordre_mode":mode,
              "kan":{"margin":has_margin,"geografi":has_geo,"tid":has_time,"levering":has_frag,"b2b":has_b2b}},
      "maaned":sorted(mnd.items()),
      "kategori":[(k,round(v),round(kdb[k]/v*100,1) if (has_margin and v) else None,round(kq[k])) for k,v in top(kr,30)],
      "maerke":[(k,round(v),round(mdb[k]/v*100,1) if (has_margin and v) else None) for k,v in top(mr,20)],
      "top_omsaetning":[(n,round(v)) for n,v in top(prod_rev)],
      "top_antal":[(n,round(v)) for n,v in top(prod_qty)],
      "prisjustering":[(n,round(mp,1),round(r),round(q)) for n,mp,r,q in prisjust],
      "genbestil":genbestil[:15],"dodt":dodt[:20],
      "geografi":[(a,round(v),omr_ord[a],round(omr_afh[a]/max(1,omr_ord[a])*100)) for a,v in omr] if has_geo else [],
      "byer":[(b,c,round(r)) for b,(c,r) in topbyer] if has_geo else [],
      "hvad_hvor":hvad if has_geo else [],
      "levering":{"afhentning":afh,"forsendelse":send} if has_frag else None,
      "kunder":[(k,round(v)) for k,v in top(kc)],"firmakunder":[(k,round(v)) for k,v in top(fc,10)] if has_b2b else [],
      "b2b":{"b2b":round(b2b),"privat":round(priv)} if has_b2b else None,
      "kombinationer":[(f"{a} + {b}",c) for (a,b),c in top(combo)],
      "timing":{"ugedag":[DOWc.get(i,0) for i in range(7)],"time":[hourc.get(h,0) for h in range(6,22)]} if has_time else None,
    }
