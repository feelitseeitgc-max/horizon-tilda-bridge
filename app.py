#!/usr/bin/env python3
"""Tilda -> GetCourse lead bridge.

Tilda form webhook recipient: POST /tilda-lead
Forwards Name/Email to the GetCourse API (creates the user or refreshes
an existing one).

Env:
  GETCOURSE_API_KEY  secret key from GetCourse account settings -> API (required)
  GETCOURSE_HOST     e.g. academy.arghorizon.com (default)
  GETCOURSE_GROUP    optional GetCourse group name for quiz leads
  BRIDGE_SECRET      optional shared secret; Tilda must call /tilda-lead?secret=...
"""
import base64
import json
import logging
import os

import requests
from flask import Flask, jsonify, request

app = Flask(__name__)
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s"
)
log = logging.getLogger("tilda-bridge")

GC_KEY = os.environ.get("GETCOURSE_API_KEY", "")
GC_HOST = os.environ.get("GETCOURSE_HOST", "academy.arghorizon.com")
GC_GROUP = os.environ.get("GETCOURSE_GROUP", "")
BRIDGE_SECRET = os.environ.get("BRIDGE_SECRET", "")


def pick(data, *names):
    for n in names:
        v = data.get(n)
        if isinstance(v, str) and v.strip():
            return v.strip()
    return ""


@app.post("/tilda-lead")
def tilda_lead():
    if BRIDGE_SECRET and request.args.get("secret") != BRIDGE_SECRET:
        return jsonify(ok=False, error="forbidden"), 403

    data = {}
    if request.is_json:
        data = request.get_json(silent=True) or {}
    for k, v in request.form.items():
        data.setdefault(k, v)
    # Tilda may wrap fields; be liberal with names
    email = pick(data, "Email", "email", "E-mail", "e-mail", "Email address")
    name = pick(data, "Name", "name", "first_name", "Имя")

    log.info("lead received: name=%r has_email=%s fields=%s",
             name, bool(email), sorted(data.keys()))
    if not email:
        return jsonify(ok=True, note="no email, skipped"), 200
    if not GC_KEY:
        log.error("GETCOURSE_API_KEY is not set")
        return jsonify(ok=False, error="getcourse not configured"), 200

    user = {"email": email, "first_name": name}
    if GC_GROUP:
        user["group_name"] = [GC_GROUP]
    params = base64.b64encode(
        json.dumps(
            {"user": user, "system": {"refresh_if_exists": 1}}, ensure_ascii=False
        ).encode("utf-8")
    ).decode("ascii")

    try:
        r = requests.post(
            f"https://{GC_HOST}/pl/api/users",
            data={"action": "add", "key": GC_KEY, "params": params},
            timeout=20,
        )
        log.info("getcourse -> HTTP %s: %s", r.status_code, r.text[:400])
    except Exception:
        log.exception("getcourse request failed")

    # Always 200 so Tilda does not retry-spam on transient errors.
    return jsonify(ok=True), 200


@app.get("/health")
def health():
    return jsonify(ok=True, getcourse_configured=bool(GC_KEY))


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))
