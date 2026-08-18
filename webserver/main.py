"""Deliberately vulnerable demo shop -- the target the proxy protects.

WARNING: every database query in this app is built by string interpolation on
purpose. It is the lab target for the SQL-injection detector and must never be
exposed to a network you do not control. Bind to localhost only.

Run:  python webserver/main.py    (listens on 127.0.0.1:5000)
"""

# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Silas Helgesson


from __future__ import annotations

import os

from flask import Flask, abort, request

from database.db_handler import close_db, ensure_db
from router import router

app = Flask(__name__)

# Demo value only -- set PROXY_SECRET to the same string on both processes.
PROXY_SECRET = os.environ.get("PROXY_SECRET", "insecure-dev-secret")
# Set REQUIRE_PROXY=1 to reject traffic that did not come through the proxy.
# Off by default so the unprotected baseline can be attacked directly.
REQUIRE_PROXY = os.environ.get("REQUIRE_PROXY", "0") == "1"
LISTEN_PORT = int(os.environ.get("WEBSERVER_PORT", "5000"))


@app.before_request
def require_proxy():
    """Reject anything that didn't come through the proxy."""
    if not REQUIRE_PROXY:
        return
    if request.headers.get("X-Proxy-Secret") != PROXY_SECRET:
        abort(403, description="Direct access is not allowed -- go through the proxy.")


app.register_blueprint(router)
app.teardown_appcontext(close_db)


if __name__ == "__main__":
    ensure_db()
    print(f"[webserver] require_proxy={REQUIRE_PROXY} port={LISTEN_PORT}")
    app.run(host="127.0.0.1", port=LISTEN_PORT)
