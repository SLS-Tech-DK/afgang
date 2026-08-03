"""Tests for webfetch — HTML-strip + fetch_text (mock urlopen)."""
import sys, io, webfetch

ok = True
def chk(c, m):
    global ok
    if not c: ok=False; print("FEJL:", m)

# strip html
t = webfetch._strip_html("<h1>Hej</h1><p>Kaffe 99 kr</p><script>x=1</script><style>a{}</style>")
chk("Hej" in t and "Kaffe 99 kr" in t, "strip beholder tekst")
chk("x=1" not in t and "a{}" not in t, "strip fjerner script/style")
chk("<" not in t, "ingen tags tilbage")

# fetch_text ok (mock urlopen)
class FakeResp:
    def __init__(self, data): self._d=data
    def read(self, n=None): return self._d
    def __enter__(self): return self
    def __exit__(self,*a): return False
def fake_ok(req, timeout=0): return FakeResp(b"<html><body><p>Testside med kaffe</p></body></html>")
webfetch.urllib.request.urlopen = fake_ok
r = webfetch.fetch_text("minshop.dk")
chk(r["ok"] is True, "fetch ok")
chk("Testside med kaffe" in r["text"], "fetch tekst udtrukket")
chk(r["url"].startswith("https://"), "scheme tilføjet")

# fetch_text fejl → pæn, ingen exception
def fake_err(req, timeout=0): raise OSError("nede")
webfetch.urllib.request.urlopen = fake_err
r2 = webfetch.fetch_text("dør.dk")
chk(r2["ok"] is False and "error" in r2, "fetch-fejl håndteres pænt")

# tom url
chk(webfetch.fetch_text("")["ok"] is False, "tom url pæn fejl")

print("RESULTAT:", "OK" if ok else "FEJL")
sys.exit(0 if ok else 1)
