"""
SLS Tech · Afgang — offentlig gateway foran den lukkede motor.
Browseren kalder DENNE (offentlig, nøgle-beskyttet). Gateway'en kalder
den private afgang-motorer server-til-server med et identity-token, så
selve motoren aldrig er åben. Payment-gating lægges ovenpå senere (Stripe).
"""
from __future__ import annotations
import os, json, urllib.request, urllib.error
import google.auth.transport.requests
import google.oauth2.id_token

MOTOR_URL = os.environ["MOTOR_URL"].rstrip("/")
GATEWAY_KEY = os.environ.get("GATEWAY_KEY", "")
ALLOW_ORIGIN = os.environ.get("ALLOW_ORIGIN", "*")


def _cors(h=None):
    h = h or {}
    h.update({
        "Access-Control-Allow-Origin": ALLOW_ORIGIN,
        "Access-Control-Allow-Methods": "POST, OPTIONS",
        "Access-Control-Allow-Headers": "Content-Type, X-Afgang-Key",
    })
    return h


def _json(payload, code):
    return (json.dumps(payload, ensure_ascii=False),
            code, _cors({"Content-Type": "application/json; charset=utf-8"}))


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
    try:
        auth_req = google.auth.transport.requests.Request()
        token = google.oauth2.id_token.fetch_id_token(auth_req, MOTOR_URL)
    except Exception as e:
        return _json({"ok": False, "error": f"Auth mod motor fejlede: {e}"}, 502)
    data = json.dumps(body).encode("utf-8")
    req = urllib.request.Request(
        MOTOR_URL + "/", data=data,
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
        method="POST")
    try:
        with urllib.request.urlopen(req, timeout=150) as r:
            return (r.read().decode("utf-8"), r.status,
                    _cors({"Content-Type": "application/json; charset=utf-8"}))
    except urllib.error.HTTPError as e:
        return (e.read().decode("utf-8"), e.code,
                _cors({"Content-Type": "application/json; charset=utf-8"}))
    except Exception as e:
        return _json({"ok": False, "error": f"Motor-kald fejlede: {e}"}, 502)
