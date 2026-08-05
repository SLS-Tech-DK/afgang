#!/usr/bin/env bash
# Afgang · scenarie-test af hele motor-kæden. Kør i Cloud Shell.
# Sætter selv URL+TOKEN. Printer PASS/FAIL pr. scenarie + samlet.
set -u
URL=$(gcloud functions describe afgang-motorer --gen2 --region=europe-north1 --format="value(serviceConfig.uri)")
TOKEN=$(gcloud auth print-identity-token)
PASS=0; FAIL=0
post(){ curl -s -X POST -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" --data "$2" "$URL/$1"; }
# check <navn> <json-svar> <python-udtryk der printer 'OK'/'FAIL'>
chk(){ local name="$1"; local out; out=$(python3 -c "$3" 2>/dev/null <<<"$2"); 
  if [ "$out" = "OK" ]; then echo "PASS  $name"; PASS=$((PASS+1)); else echo "FAIL  $name  → $(echo "$2" | head -c 160)"; FAIL=$((FAIL+1)); fi; }

echo "== SUNDHED =="
chk "health" "$(curl -s -H "Authorization: Bearer $TOKEN" "$URL/")" \
 'import sys,json;d=json.load(sys.stdin);print("OK" if d.get("ok") and len(d.get("products",[]))>=10 else "FAIL")'

# lille inline prøvedata til butiks (embedded ordre-format)
VARE='Varenummer;Navn;Primær kategori;Mærke;Pris;Indkøbspris;Lager\n1;Kaffe;Kaffe;A;100;60;40\n2;Filter;Tilbehør;B;30;10;200\n3;Kande;Udstyr;A;299;180;5'
ORDRE='Ordrenr;Produkt varenumre;Produkt titler;Ordredato;Kunde postnr.;Kunde firma;Fragtmetode\n1;1|||2;Kaffe (2)|||Filter (1);01-03-2026;9300;;Afhentning\n2;1|||3;Kaffe (1)|||Kande (1);05-03-2026;2100;Firma ApS;Levering\n3;2;Filter (3);20-03-2026;8000;;Levering'
BODY_OK=$(python3 -c "import json;print(json.dumps({'vare_csv':'$VARE'.replace(chr(92)+'n',chr(10)),'ordre_csv':'$ORDRE'.replace(chr(92)+'n',chr(10))}))")

echo "== HAPPY PATH: butiks demo (5) =="
for P in salgsanalyse indkobsanalyse lageranalyse kundeanalyse fuld_butiksanalyse; do
  chk "$P demo" "$(post $P "{\"type\":\"$P\",\"demo\":true}")" \
   'import sys,json;d=json.load(sys.stdin).get("result",{});print("OK" if d.get("html") else "FAIL")'
done

echo "== HAPPY PATH: butiks rigtig data (5) =="
for P in salgsanalyse indkobsanalyse lageranalyse kundeanalyse fuld_butiksanalyse; do
  B=$(python3 -c "import json,sys;b=json.load(open('/dev/stdin'));b['type']='$P';print(json.dumps(b))" <<<"$BODY_OK")
  chk "$P rigtig" "$(post $P "$B")" \
   'import sys,json;d=json.load(sys.stdin).get("result",{});m=d.get("meta",{});print("OK" if d.get("html") and m.get("omsætning") else "FAIL")'
done

echo "== EDGE/ERROR: tomt + manglende felter =="
chk "butiks tom ordre → pæn fejl" "$(post fuld_butiksanalyse '{"type":"fuld_butiksanalyse","vare_csv":"Varenummer;Navn\n1;X","ordre_csv":"Ordrenr\n"}')" \
 'import sys,json;d=json.load(sys.stdin);print("OK" if (not d.get("ok")) or d.get("result",{}).get("error") else "FAIL")'
chk "ukendt type → 404-agtig fejl" "$(post ukendt '{"type":"ukendt"}')" \
 'import sys,json;d=json.load(sys.stdin);print("OK" if not d.get("ok") else "FAIL")'

echo "== KONKURRENT (går på nettet, ~10-30s) =="
chk "konkurrent 2 domæner" "$(post konkurrentanalyse '{"type":"konkurrentanalyse","domain":"peterlarsenkaffe.dk","competitors":["kaffekapslen.dk"]}')" \
 'import sys,json;d=json.load(sys.stdin).get("result",{});print("OK" if d.get("html") and d.get("analyse") else "FAIL")'

echo "== AI-SYNLIGHED (live Gemini) =="
chk "ai_synlighed brand+field" "$(post ai_synlighed '{"type":"ai_synlighed","brand":"MinShop","field":"kaffe","competitors":["Peter Larsen Kaffe"]}')" \
 'import sys,json;d=json.load(sys.stdin).get("result",{});print("OK" if d.get("html") and "geo" in d else "FAIL")'

echo "== REVIEW =="
chk "review rating+tekst" "$(post review_analyse '{"type":"review_analyse","csv":"Rating;Tekst\n5;Super\n1;Dårlig levering\n2;Sen"}')" \
 'import sys,json;d=json.load(sys.stdin).get("result",{});print("OK" if d.get("html") else "FAIL")'

echo ""
echo "===================="
echo "RESULTAT: $PASS PASS · $FAIL FAIL"
[ $FAIL -eq 0 ] && echo "ALT GRØNT ✓" || echo "Se FAIL-linjer ovenfor. Send dem til Claude."
