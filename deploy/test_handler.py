"""Test af HTTP-handleren: sti-routing rammer rette produkt, GET-sundhedstjek,
og bagud-kompatibelt {"type": ...} i body. Importerer main (alle motorer)."""
import io, csv, json
from main import handler, REGISTRY


class FakeRequest:
    def __init__(self, method="POST", path="/", body=None):
        self.method = method
        self.path = path
        self._body = body or {}
    def get_json(self, silent=True):
        return self._body


def _parse(resp):
    text, code, _headers = resp
    return json.loads(text), code


ok = True
def check(cond, msg):
    global ok
    if not cond:
        ok = False
        print("FEJL:", msg)


# salgs-CSV til POST-tests
buf = io.StringIO(); csv.writer(buf).writerows(
    [["Order ID", "Lineitem name", "Lineitem quantity", "Lineitem price"],
     ["1", "Kaffe", "2", "79.50"], ["1", "Filter", "1", "29.00"], ["2", "Kaffe", "1", "79.50"]])
sales_csv = buf.getvalue()

# 1. POST /salgsanalyse (sti bestemmer type, ingen type i body)
data, code = _parse(handler(FakeRequest(path="/salgsanalyse", body={"csv": sales_csv})))
check(code == 200 and data["type"] == "salgsanalyse" and "bestsellers" in data["result"], "POST /salgsanalyse")

# 2. POST /butiksanalyse (premium via sti)
data, code = _parse(handler(FakeRequest(path="/butiksanalyse", body={"csv": sales_csv})))
check(code == 200 and data["type"] == "butiksanalyse" and "handlingsplan" in data["result"], "POST /butiksanalyse")

# 3. Kælenavn /butiksrontgen → butiksanalyse
data, code = _parse(handler(FakeRequest(path="/butiksrontgen", body={"csv": sales_csv})))
check(data["type"] == "butiksanalyse", "POST /butiksrontgen alias")

# 4. Bagud-kompatibelt: body-type vinder over sti
data, code = _parse(handler(FakeRequest(path="/salgsanalyse", body={"type": "kundeanalyse", "csv": sales_csv})))
check(data["type"] == "kundeanalyse", "body-type vinder over sti")

# 5. GET / → sundhedstjek med produktliste
data, code = _parse(handler(FakeRequest(method="GET", path="/")))
check(code == 200 and set(data["products"]) == set(REGISTRY), "GET / sundhedstjek")

# 6. GET på ukendt sti → 404
data, code = _parse(handler(FakeRequest(method="GET", path="/findes-ikke")))
check(code == 404 and data["ok"] is False, "GET ukendt sti → 404")

# 7. POST / uden type og uden sti → pæn fejl
data, code = _parse(handler(FakeRequest(path="/", body={"csv": sales_csv})))
check(code == 400 and data["ok"] is False, "POST uden type/sti → 400")

print("Handler dækker", len(REGISTRY), "produkt-stier.")
print("RESULTAT:", "✓ OK" if ok else "✗ FEJL")
import sys; sys.exit(0 if ok else 1)
