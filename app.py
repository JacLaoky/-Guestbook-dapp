import os
import sqlite3

from flask import Flask, jsonify, render_template, request

app = Flask(__name__)

# Set these in Render -> Environment
CONTRACT_ADDRESS = os.environ.get("CONTRACT_ADDRESS", "")
RPC_URL = os.environ.get("RPC_URL", "https://ethereum-sepolia-rpc.publicnode.com")
DB_PATH = os.environ.get("DB_PATH", "messages.db")


# ---------- Database (SQLite, built into Python) ----------

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # rows behave like dicts
    return conn


def init_db():
    with get_db() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                content    TEXT NOT NULL,
                sender     TEXT NOT NULL,
                tx_hash    TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)


init_db()


# ---------- Pages ----------

@app.route("/")
def index():
    return render_template("index.html", contract_address=CONTRACT_ADDRESS, rpc_url=RPC_URL)


# ---------- API: list / add / delete ----------

@app.route("/api/messages", methods=["GET"])
def list_messages():
    with get_db() as conn:
        rows = conn.execute("SELECT * FROM messages ORDER BY id DESC").fetchall()
    return jsonify([dict(r) for r in rows])


@app.route("/api/messages", methods=["POST"])
def add_message():
    data = request.get_json() or {}
    content = (data.get("content") or "").strip()
    sender = (data.get("sender") or "").strip()
    if not content or not sender:
        return jsonify({"error": "content and sender are required"}), 400

    with get_db() as conn:
        cur = conn.execute(
            "INSERT INTO messages (content, sender, tx_hash) VALUES (?, ?, ?)",
            (content, sender, data.get("tx_hash")),
        )
    return jsonify({"id": cur.lastrowid}), 201


@app.route("/api/messages/<int:message_id>", methods=["DELETE"])
def delete_message(message_id):
    with get_db() as conn:
        cur = conn.execute("DELETE FROM messages WHERE id = ?", (message_id,))
    if cur.rowcount == 0:
        return jsonify({"error": "not found"}), 404
    return jsonify({"deleted": message_id})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=True)
