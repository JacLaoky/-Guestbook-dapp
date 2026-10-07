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
        # Remembers the last on-chain updateCount already saved to history,
        # so a deleted record is never synced back in again
        conn.execute("""
            CREATE TABLE IF NOT EXISTS sync_state (
                id                INTEGER PRIMARY KEY CHECK (id = 1),
                last_update_count INTEGER NOT NULL
            )
        """)
        conn.execute("INSERT OR IGNORE INTO sync_state (id, last_update_count) VALUES (1, 0)")


def last_synced_count(conn):
    return conn.execute("SELECT last_update_count FROM sync_state WHERE id = 1").fetchone()[0]


def mark_synced(conn, update_count):
    conn.execute(
        "UPDATE sync_state SET last_update_count = MAX(last_update_count, ?) WHERE id = 1",
        (update_count,),
    )


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
        if data.get("update_count") is not None:
            mark_synced(conn, int(data["update_count"]))
    return jsonify({"id": cur.lastrowid}), 201


@app.route("/api/messages/sync", methods=["POST"])
def sync_message():
    """Record the current on-chain message if it was changed outside this website
    (e.g. in Remix or Etherscan). Uses the contract's updateCount so each on-chain
    update is saved at most once, even if its record is deleted later."""
    data = request.get_json() or {}
    content = (data.get("content") or "").strip()
    sender = (data.get("sender") or "").strip()
    update_count = data.get("update_count")
    if not content or not sender or update_count is None:
        return jsonify({"added": False})

    update_count = int(update_count)
    with get_db() as conn:
        if update_count <= last_synced_count(conn):
            return jsonify({"added": False})
        conn.execute(
            "INSERT INTO messages (content, sender) VALUES (?, ?)", (content, sender)
        )
        mark_synced(conn, update_count)
    return jsonify({"added": True})


@app.route("/api/messages/<int:message_id>", methods=["DELETE"])
def delete_message(message_id):
    with get_db() as conn:
        cur = conn.execute("DELETE FROM messages WHERE id = ?", (message_id,))
    if cur.rowcount == 0:
        return jsonify({"error": "not found"}), 404
    return jsonify({"deleted": message_id})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=True)
