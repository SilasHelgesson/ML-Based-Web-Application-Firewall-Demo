"""Filtering reverse proxy.

Sits in front of the (deliberately vulnerable) web server, scores every
inbound query string and POST body with the trained SQLi classifier, and
returns 403 when the attack probability crosses the threshold. Everything
else is forwarded unchanged, with a shared secret header so the backend can
refuse traffic that bypassed the proxy.

Run:  python proxy/main.py        (listens on :8080, forwards to :5000)
"""

# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Silas Helgesson


from __future__ import annotations

import os
import sys
from pathlib import Path

import requests
from flask import Flask, Response, abort, request

# The saved pipeline unpickles `HandcraftedFeatures` from a top-level
# `sqli_features` module, so ml/ has to be on sys.path before the import below.
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "ml"))

from model import SqliDetector  # noqa: E402

# --- configuration (override via environment) ------------------------------
BACKEND = os.environ.get("BACKEND_URL", "http://127.0.0.1:5000")
MODEL_PATH = os.environ.get("SQLI_MODEL", str(ROOT / "ml" / "sqli_model.joblib"))
THRESHOLD = float(os.environ.get("SQLI_THRESHOLD", "0.9"))
# Demo value only -- set PROXY_SECRET to the same string on both processes.
PROXY_SECRET = os.environ.get("PROXY_SECRET", "insecure-dev-secret")
LISTEN_PORT = int(os.environ.get("PROXY_PORT", "8080"))

# Hop-by-hop headers that must not be copied from the backend response.
EXCLUDED_RESPONSE_HEADERS = {
    "content-encoding",
    "content-length",
    "transfer-encoding",
    "connection",
}

app = Flask(__name__)
detector = SqliDetector(MODEL_PATH, THRESHOLD)


def inspect(req) -> None:
    """Score the request's user-controlled input; abort with 403 on attack."""
    payload_parts = []

    if req.args:
        payload_parts.append(
            "&".join(f"{k}={v}" for k, v in req.args.items(multi=True))
        )

    if req.method == "POST":
        body = req.get_data(as_text=True)
        if body:
            payload_parts.append(body)

    if not payload_parts:
        return

    payload = "\n".join(payload_parts)
    result = detector.predict(payload)
    app.logger.info(
        "%s %s p=%.3f %s", req.method, req.path,
        result["attack_probability"], result["label"],
    )
    if result["is_attack"]:
        abort(403)


@app.route("/", defaults={"path": ""},
           methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS", "HEAD"])
@app.route("/<path:path>",
           methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS", "HEAD"])
def proxy(path):
    inspect(request)

    headers = {k: v for k, v in request.headers if k.lower() != "host"}
    headers["X-Proxy-Secret"] = PROXY_SECRET

    backend_resp = requests.request(
        method=request.method,
        url=f"{BACKEND}/{path}",
        headers=headers,
        params=request.args,
        data=request.get_data(),
        cookies=request.cookies,
        allow_redirects=False,
    )

    response_headers = [
        (k, v) for k, v in backend_resp.headers.items()
        if k.lower() not in EXCLUDED_RESPONSE_HEADERS
    ]
    return Response(backend_resp.content, backend_resp.status_code, response_headers)


if __name__ == "__main__":
    print(f"[proxy] model={MODEL_PATH} threshold={THRESHOLD}")
    print(f"[proxy] listening on :{LISTEN_PORT} -> {BACKEND}")
    app.run(host="127.0.0.1", port=LISTEN_PORT)
