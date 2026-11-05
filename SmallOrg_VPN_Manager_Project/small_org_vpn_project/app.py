import base64
import ipaddress
import os
import sqlite3
from datetime import datetime, timezone
from functools import wraps
from pathlib import Path

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.x25519 import X25519PrivateKey
from flask import Flask, flash, redirect, render_template, request, send_file, session, url_for

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = Path(os.getenv("DATABASE_PATH", BASE_DIR / "vpn_manager.db"))

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "dev-only-change-this-secret")
app.config["MAX_CONTENT_LENGTH"] = 1 * 1024 * 1024

ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "ChangeMe123!")
VPN_ENDPOINT = os.getenv("VPN_ENDPOINT", "vpn.example.com:51820")
SERVER_PUBLIC_KEY = os.getenv("SERVER_PUBLIC_KEY", "REPLACE_WITH_SERVER_PUBLIC_KEY")
VPN_NETWORK = os.getenv("VPN_NETWORK", "10.8.0.0/24")
DNS_SERVER = os.getenv("DNS_SERVER", "1.1.1.1")
CLIENT_ALLOWED_IPS = os.getenv("CLIENT_ALLOWED_IPS", "10.8.0.0/24")
KEEPALIVE = os.getenv("PERSISTENT_KEEPALIVE", "25")


def db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with db() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS peers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT,
                address TEXT NOT NULL UNIQUE,
                private_key TEXT NOT NULL,
                public_key TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
        """)


def login_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if not session.get("logged_in"):
            return redirect(url_for("login"))
        return fn(*args, **kwargs)
    return wrapper


def generate_keypair():
    private_key = X25519PrivateKey.generate()
    private_bytes = private_key.private_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PrivateFormat.Raw,
        encryption_algorithm=serialization.NoEncryption()
    )
    public_bytes = private_key.public_key().public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw
    )
    return (
        base64.b64encode(private_bytes).decode("ascii"),
        base64.b64encode(public_bytes).decode("ascii")
    )


def next_client_ip(conn):
    network = ipaddress.ip_network(VPN_NETWORK, strict=False)
    used = {row["address"] for row in conn.execute("SELECT address FROM peers")}
    for host in network.hosts():
        candidate = f"{host}/32"
        if host != network.network_address and candidate not in used:
            return candidate
    raise ValueError("No free client IP addresses remain in VPN_NETWORK.")


def build_client_config(peer):
    return f"""[Interface]
PrivateKey = {peer['private_key']}
Address = {peer['address']}
DNS = {DNS_SERVER}

[Peer]
PublicKey = {SERVER_PUBLIC_KEY}
Endpoint = {VPN_ENDPOINT}
AllowedIPs = {CLIENT_ALLOWED_IPS}
PersistentKeepalive = {KEEPALIVE}
"""


@app.route("/")
def index():
    if not session.get("logged_in"):
        return redirect(url_for("login"))
    with db() as conn:
        peers = conn.execute(
            "SELECT id, name, email, address, public_key, created_at FROM peers ORDER BY id DESC"
        ).fetchall()
    return render_template(
        "index.html", peers=peers, endpoint=VPN_ENDPOINT,
        server_key_ready=SERVER_PUBLIC_KEY != "REPLACE_WITH_SERVER_PUBLIC_KEY"
    )


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "")
        password = request.form.get("password", "")
        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session.clear()
            session["logged_in"] = True
            return redirect(url_for("index"))
        flash("Incorrect username or password.", "error")
    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


@app.route("/peers/add", methods=["POST"])
@login_required
def add_peer():
    name = request.form.get("name", "").strip()
    email = request.form.get("email", "").strip()
    if not name or len(name) > 80 or len(email) > 120:
        flash("Enter a valid name (max 80 characters) and email (max 120 characters).", "error")
        return redirect(url_for("index"))

    try:
        with db() as conn:
            address = next_client_ip(conn)
            private_key, public_key = generate_keypair()
            conn.execute(
                """INSERT INTO peers (name, email, address, private_key, public_key, created_at)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (name, email, address, private_key, public_key,
                 datetime.now(timezone.utc).isoformat(timespec="seconds"))
            )
        flash(f"Peer created for {name}. Download its configuration and deliver it securely.", "success")
    except (ValueError, sqlite3.IntegrityError) as exc:
        flash(str(exc), "error")
    return redirect(url_for("index"))


@app.route("/peers/<int:peer_id>/config")
@login_required
def download_config(peer_id):
    with db() as conn:
        peer = conn.execute("SELECT * FROM peers WHERE id = ?", (peer_id,)).fetchone()
    if not peer:
        flash("Peer not found.", "error")
        return redirect(url_for("index"))
    config_path = BASE_DIR / "generated" / f"peer-{peer_id}.conf"
    config_path.parent.mkdir(exist_ok=True)
    config_path.write_text(build_client_config(peer), encoding="utf-8")
    return send_file(config_path, as_attachment=True, download_name=f"{peer['name'].replace(' ', '_')}.conf")


@app.route("/peers/<int:peer_id>/server-snippet")
@login_required
def server_snippet(peer_id):
    with db() as conn:
        peer = conn.execute(
            "SELECT name, address, public_key FROM peers WHERE id = ?", (peer_id,)
        ).fetchone()
    if not peer:
        flash("Peer not found.", "error")
        return redirect(url_for("index"))
    snippet = f"""# Client: {peer['name']}
[Peer]
PublicKey = {peer['public_key']}
AllowedIPs = {peer['address']}
"""
    from flask import Response
    return Response(snippet, mimetype="text/plain",
                    headers={"Content-Disposition": f'attachment; filename="peer-{peer_id}-server-peer.conf"'})


@app.route("/peers/<int:peer_id>/delete", methods=["POST"])
@login_required
def delete_peer(peer_id):
    with db() as conn:
        conn.execute("DELETE FROM peers WHERE id = ?", (peer_id,))
    flash("Peer removed from this manager. Also remove its [Peer] entry from the live WireGuard server.", "success")
    return redirect(url_for("index"))


@app.route("/health")
def health():
    return {"status": "ok", "service": "Small Organisation VPN Manager"}


init_db()

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=int(os.getenv("PORT", "5000")), debug=False)
