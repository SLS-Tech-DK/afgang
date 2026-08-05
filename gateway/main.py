"""
SLS Tech · Afgang — offentlig gateway + VANDTÆT betalings-gate.
Browseren kalder denne (offentlig, nøgle-beskyttet). Regler:
- demo:true  → gratis, forwardes frit.
- rigtig kørsel → kræver 'access_token' der er BETALT og ikke opbrugt (tjekkes i
  Supabase afgang_orders, service-role). Match på produkt-type. Forbruges pr. kørsel.
- Motoren (afgang-motorer) er ren compute; gaten sidder her.
Håndhævelse aktiveres når SUPABASE_URL + SUPABASE_SERVICE_KEY er sat i env.
Uden dem: gaten er åben (til demo/test før Stripe).
"""
from __future__ import annotations
import os, json, urllib.request, urllib.error
import google.auth.transport.requests
import google.oauth2.id_token

MOTOR_URL = os.environ["MOTOR_URL"].rstrip("/")
GATEWAY_KEY = os.environ.get("GATEWAY_KEY", "")
ALLOW_ORIGIN = os.environ.get("ALLOW_ORIGIN", "*")
SB_URL = os.environ.get("SUPABASE_URL", "").rstrip("/")
SB_KEY = os.environ.get("SUPABASE_SERVICE_KEY", "")
FREE = {"spoerg_data"}  # Q&A om egne data — gratis efter køb (ingen ekstra gate)


def _cors(h=None):
    h = h or {}
    h.update({"Access-Control-Allow-Origin": ALLOW_ORIGIN,
              "Access-Control-Allow-Methods": "POST, OPTIONS",
              "Access-Control-Allow-Headers": "Content-Type, X-Afgang-Key"})
    return h


def _json(payload, code):
    return (json.dumps(payload, ensure_ascii=False), code,
            _cors({"Content-Type": "application/json; charset=utf-8"}))


def _sb(method, path, body=None):
    req = urllib.request.Request(
        f"{SB_URL}/rest/v1/{path}",
        data=(json.dumps(body).encode() if body is not None else None),
        headers={"apikey": SB_KEY, "Authorization": f"Bearer {SB_KEY}",
                 "Content-Type": "application/json", "Prefer": "return=representation"},
        method=method)
    with urllib.request.urlopen(req, timeout=15) as r:
        return json.loads(r.read().decode() or "[]")


def _payment_ok(body):
    """(ok, fejl). demo=gratis. Ellers kræves betalt, ubrugt token der matcher produkt."""
    if body.get("demo"):
        return True, None
    if (body.get("type") or "") in FREE:
        return True, None
    if not (SB_URL and SB_KEY):
        return True, None  # ikke konfigureret endnu → åben (før Stripe)
    token = body.get("access_token", "")
    if not token:
        return False, "Betaling kræves — mangler adgangsnøgle."
    try:
        rows = _sb("GET", f"afgang_orders?access_token=eq.{token}&select=id,product,status,runs_allowed,runs_used")
    except Exception as e:
        return False, f"Kunne ikke verificere betaling: {e}"
    if not rows:
        return False, "Ugyldig adgangsnøgle."
    o = rows[0]
    if o.get("status") != "paid":
        return False, "Ordren er ikke betalt."
    if int(o.get("runs_used", 0)) >= int(o.get("runs_allowed", 1)):
        return False, "Adgangen er allerede brugt."
    if o.get("product") and o["product"] != body.get("type"):
        return False, "Adgangsnøglen gælder et andet produkt."
    # forbrug én kørsel
    try:
        used = int(o.get("runs_used", 0)) + 1
        patch = {"runs_used": used, "used_at": "now()"}
        if used >= int(o.get("runs_allowed", 1)):
            patch["status"] = "brugt"
        _sb("PATCH", f"afgang_orders?id=eq.{o['id']}", patch)
    except Exception:
        pass  # kørslen tillades; forbrug bedst-effort
    return True, None


def handler(request):
    if request.method == "OPTIONS":
        return ("", 204, _cors())
    if request.method != "POST":
        return _json({"ok": False, "error": "Brug POST"}, 405)
    key = request.headers.get("X-Afgang-Key", "")
    if not key:
        try: key = request.args.get("key", "")
        except Exception: key = ""
    if GATEWAY_KEY and key != GATEWAY_KEY:
        return _json({"ok": False, "error": "Ugyldig eller manglende nøgle"}, 401)
    try:
        body = request.get_json(silent=True) or {}
    except Exception:
        body = {}
    # Hent adgangsnøgle efter Stripe-redirect (session_id -> token)
    if body.get("session_id") and not body.get("type"):
        if not (SB_URL and SB_KEY):
            return _json({"ok": False, "error": "Betaling ikke konfigureret"}, 400)
        try:
            rows = _sb("GET", f"afgang_orders?stripe_session=eq.{body['session_id']}&select=access_token,product,status")
        except Exception as e:
            return _json({"ok": False, "error": str(e)}, 502)
        if not rows or rows[0].get("status") != "paid":
            return _json({"ok": False, "error": "Ordre ikke fundet eller ikke betalt endnu"}, 404)
        return _json({"ok": True, "access_token": rows[0]["access_token"], "product": rows[0]["product"]}, 200)
    ok, err = _payment_ok(body)
    if not ok:
        return _json({"ok": False, "error": err, "betaling_kraevet": True}, 402)
    try:
        auth_req = google.auth.transport.requests.Request()
        tok = google.oauth2.id_token.fetch_id_token(auth_req, MOTOR_URL)
    except Exception as e:
        return _json({"ok": False, "error": f"Auth mod motor fejlede: {e}"}, 502)
    data = json.dumps(body).encode("utf-8")
    req = urllib.request.Request(
        MOTOR_URL + "/", data=data,
        headers={"Authorization": f"Bearer {tok}", "Content-Type": "application/json"}, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=150) as r:
            return (r.read().decode("utf-8"), r.status,
                    _cors({"Content-Type": "application/json; charset=utf-8"}))
    except urllib.error.HTTPError as e:
        return (e.read().decode("utf-8"), e.code, _cors({"Content-Type": "application/json; charset=utf-8"}))
    except Exception as e:
        return _json({"ok": False, "error": f"Motor-kald fejlede: {e}"}, 502)
