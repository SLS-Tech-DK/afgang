#!/usr/bin/env python3
"""
SLS Tech · Afgang — generér ægte demo-output fra den live motor.
Kører hvert af de 14 produkter gennem den deployede funktion på de
rigtige eksempelfiler, og gemmer svarene i demo_output.json.
Frontend bager dette ind som frosset "Vis eksempel"-output.

Brug (i Cloud Shell, fra ~/afgang):
  export URL=$(gcloud functions describe afgang-motorer --gen2 --region=europe-north1 --format="value(serviceConfig.uri)")
  export TOKEN=$(gcloud auth print-identity-token)
  python3 tools/gen_demo.py
"""
import json, os, sys, urllib.request, urllib.error

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EKS = os.path.join(ROOT, "eksempler")
URL = os.environ["URL"].rstrip("/")
TOKEN = os.environ["TOKEN"]

def rd(name):
    with open(os.path.join(EKS, name), encoding="utf-8") as f:
        return f.read()

def rj(name):
    return json.loads(rd(name))

# type -> request body (uden 'type', som sættes af stien)
BODIES = {
    "salgsanalyse":     {"csv": rd("ordre-eksempel.csv")},
    "indkobsanalyse":   {"csv": rd("ordre-eksempel.csv")},
    "lageranalyse":     {"csv": rd("ordre-eksempel.csv"), "stock_csv": rd("lager-eksempel.csv")},
    "kundeanalyse":     {"csv": rd("ordre-eksempel.csv")},
    "butiksanalyse":    {"csv": rd("ordre-eksempel.csv"), "stock_csv": rd("lager-eksempel.csv")},
    "konkurrentanalyse": rj("konkurrentanalyse-eksempel.json"),
    "ai_synlighed":     rj("ai-synlighed-eksempel.json"),
    "prisovervagning":  rj("prisovervagning-eksempel.json"),
    "naevner_ai_alarm": rj("naevner-ai-alarm-eksempel.json"),
    "produkttekst":     {"csv": rd("produktkatalog-eksempel.csv")},
    "review_analyse":   {"csv": rd("reviews-eksempel.csv")},
    "landingsside":     {"page_text": rd("landingsside-eksempel.txt")},
    "annonce_spild":    {"csv": rd("annoncer-eksempel.csv")},
    "soegeords_gap":    {"csv": rd("soegelog-eksempel.csv")},
}

out = {}
for t, body in BODIES.items():
    payload = json.dumps({**body, "type": t}).encode("utf-8")
    req = urllib.request.Request(
        f"{URL}/{t}", data=payload,
        headers={"Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json"},
        method="POST")
    try:
        with urllib.request.urlopen(req, timeout=150) as r:
            data = json.loads(r.read().decode("utf-8"))
        ok = data.get("ok")
        has_g = bool(data.get("forklaring", {}).get("forklaring_tekst"))
        out[t] = data
        print(f"{'OK ' if ok else 'FEJL'} {t:18} gemini={'ja' if has_g else 'nej'}")
    except urllib.error.HTTPError as e:
        print(f"FEJL {t:18} HTTP {e.code}: {e.read().decode('utf-8')[:200]}")
        out[t] = {"ok": False, "error": f"HTTP {e.code}"}
    except Exception as e:
        print(f"FEJL {t:18} {e}")
        out[t] = {"ok": False, "error": str(e)}

with open(os.path.join(ROOT, "frontend", "demo_output.json"), "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False, indent=2)
print("\nGemt til frontend/demo_output.json")
