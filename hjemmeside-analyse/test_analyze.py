#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tests for analyze.py — beviser at hvert lag-1-tjek virker, på syntetiske fixtures.
Netværksfri. Kør: python3 test_analyze.py  (0 = alle bestået)
"""
import sys
from analyze import analyze

FRONT_BAD = """<!doctype html><html lang="da"><head>
<title>Min klinik</title></head><body>
<h2>Velkommen</h2>
<p>Kort.</p>
<p>Her kommer snart en fyldestgørende beskrivelse.</p>
<img src="a.jpg">
<form><label>Name</label><input><label>Email</label><input><button>Send Email</button></form>
<script type="application/ld+json">{"@context":"https://schema.org","@type":"Organization","name":"Min klinik"}</script>
</body></html>"""

SITE_BAD = {
    "base_url": "https://daarlig.dk", "name": "Dårlig Klinik", "type": "klinik", "tech": "WordPress",
    "https": True, "robots_txt": None, "sitemap_xml": None, "llms_txt": None,
    "pages": [{"url": "https://daarlig.dk", "status": 200, "html": FRONT_BAD}],
}

_para = "<p>" + ("Vi tilbyder professionel behandling i hjertet af byen med mange års erfaring. " * 12) + "</p>"
FRONT_GOOD = f"""<!doctype html><html lang="da"><head>
<title>God Klinik — akupunktur i Aarhus</title>
<meta name="description" content="Akupunktur og zoneterapi i Aarhus. Book online.">
<script type="application/ld+json">{{"@context":"https://schema.org","@graph":[
 {{"@type":"HealthAndBeautyBusiness","name":"God Klinik","telephone":"+4512345678"}},
 {{"@type":"FAQPage"}}]}}</script>
</head><body><h1>God Klinik</h1>{_para}
<img src="a.jpg" alt="behandlingsrum"><a href="/blog/akupunktur-mod-migraene">Blog</a>
<form><label>Navn</label><input><label>Besked</label><textarea></textarea><button>Send</button></form>
</body></html>"""
BLOG_GOOD = f"""<!doctype html><html lang="da"><head><title>Akupunktur mod migræne — God Klinik</title>
<meta name="description" content="Hvad siger forskningen om akupunktur mod migræne."></head>
<body><h1>Akupunktur mod migræne</h1>{_para}<img src="b.jpg" alt="nål"></body></html>"""

SITE_GOOD = {
    "base_url": "https://god.dk", "name": "God Klinik", "type": "klinik", "tech": "WordPress",
    "https": True, "robots_txt": "User-agent: *\nSitemap: https://god.dk/sitemap.xml",
    "sitemap_xml": "<urlset><url><loc>https://god.dk/</loc></url></urlset>", "llms_txt": "# God Klinik",
    "pages": [{"url": "https://god.dk", "status": 200, "html": FRONT_GOOD},
              {"url": "https://god.dk/blog/akupunktur-mod-migraene", "status": 200, "html": BLOG_GOOD}],
}

def titles(p): return {f["title"] for f in p["_findings"]}

def run():
    checks = []
    def ok(cond, msg): checks.append((bool(cond), msg))

    # ---- BAD site ----
    b = analyze(SITE_BAD)
    bt = titles(b)
    ok(any("H1" in t for t in bt), "bad: forsiden mangler H1 fanges")
    ok(any("robots" in t.lower() for t in bt), "bad: manglende robots fanges")
    ok(any("sitemap" in t.lower() for t in bt), "bad: manglende sitemap fanges")
    ok(any("llms" in t.lower() for t in bt), "bad: manglende llms.txt fanges")
    ok(any("Organization" in t for t in bt), "bad: kun Organization-schema fanges")
    ok(any("FAQ" in t for t in bt), "bad: manglende FAQ-schema fanges")
    ok(any("meta-beskriv" in t.lower() for t in bt), "bad: manglende meta fanges")
    ok(any("placeholder" in t.lower() or "kommer snart" in t.lower() for t in bt), "bad: placeholder fanges")
    ok(any("engelsk" in t.lower() for t in bt), "bad: engelsk formular fanges")
    ok(any("alt-tekst" in t.lower() for t in bt), "bad: manglende alt-tekst fanges")
    ok(any("blog" in t.lower() for t in bt), "bad: manglende blog fanges")
    ok(b["meta"]["score"] < 60, f"bad: lav score (fik {b['meta']['score']})")
    ok(len(b["recommendations"]) >= 5, "bad: anbefalinger genereret")
    ok(b["recommendations"][0]["tag"] in ("crit", "hoej"), "bad: værste anbefaling øverst")
    ok(any("bekræft" in c["title"].lower() for c in b["lokal"]), "bad: Google-profil bekræft-kort med")

    # ---- GOOD site ----
    g = analyze(SITE_GOOD)
    gt = titles(g)
    ok(not any("H1" in t for t in gt), "good: ingen H1-fejl")
    ok(not any("robots" in t.lower() for t in gt), "good: robots ok")
    ok(not any("sitemap" in t.lower() for t in gt), "good: sitemap ok")
    ok(not any("llms" in t.lower() for t in gt), "good: llms ok")
    ok(not any("FAQ" in t for t in gt), "good: FAQ-schema ok")
    ok(not any("schema" in t.lower() for t in gt), "good: LocalBusiness-schema ok")
    ok(not any("blog" in t.lower() for t in gt), "good: blog fundet, intet fund")
    ok(not any("engelsk" in t.lower() for t in gt), "good: dansk formular ok")
    ok(not any("placeholder" in t.lower() for t in gt), "good: ingen placeholder")
    ok(g["meta"]["score"] >= 90, f"good: høj score (fik {g['meta']['score']})")

    # ---- schema parsing robustness ----
    from analyze import _schema_types, _soup
    graph = '<script type="application/ld+json">{"@graph":[{"@type":["LocalBusiness","Store"]}]}</script>'
    ok("LocalBusiness" in _schema_types(_soup(graph)), "schema: @graph + type-liste parses")
    bad_json = '<script type="application/ld+json">{ not valid json </script>'
    ok(_schema_types(_soup(bad_json)) == set(), "schema: ugyldig JSON-LD håndteres uden crash")

    # ---- report ----
    passed = sum(1 for c, _ in checks if c)
    for c, m in checks:
        print(("  OK " if c else "FAIL") + " · " + m)
    print(f"\n{passed}/{len(checks)} bestået")
    return 0 if passed == len(checks) else 1

if __name__ == "__main__":
    sys.exit(run())
