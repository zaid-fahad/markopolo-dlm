import sqlite3
import time
import sys
from flask import Flask, request, jsonify

app = Flask(__name__)
DB_FILE = f"node_{sys.argv[1] if len(sys.argv) > 1 else 'default'}.db"

def init_db():
    with sqlite3.connect(DB_FILE) as conn:
        conn.execute("CREATE TABLE IF NOT EXISTS locks (name TEXT PRIMARY KEY, holder_id TEXT, expiry REAL, token INTEGER)")
        conn.execute("CREATE TABLE IF NOT EXISTS config (key TEXT PRIMARY KEY, val INTEGER)")
        conn.execute("INSERT OR IGNORE INTO config VALUES ('last_token', 0)")

@app.route('/acquire', methods=['POST'])
def acquire():
    data = request.json
    name, client_id, ttl = data['name'], data['client_id'], data['ttl']
    now = time.monotonic()

    with sqlite3.connect(DB_FILE) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT holder_id, expiry, token FROM locks WHERE name = ?", (name,))
        row = cursor.fetchone()
        
        # Grant lock if free or expired
        if row is None or now > row['expiry']:
            cursor.execute("UPDATE config SET val = val + 1 WHERE key = 'last_token'")
            cursor.execute("SELECT val FROM config WHERE key = 'last_token'")
            new_token = cursor.fetchone()[0]
            
            cursor.execute("INSERT OR REPLACE INTO locks VALUES (?, ?, ?, ?)", 
                         (name, client_id, now + ttl, new_token))
            return jsonify({"status": "GRANTED", "token": new_token}), 200
        
        return jsonify({"status": "DENIED", "owner": row['holder_id']}), 409

@app.route('/release', methods=['POST'])
def release():
    data = request.json
    with sqlite3.connect(DB_FILE) as conn:
        # Fencing: Only delete if client_id and token match
        cursor = conn.execute("DELETE FROM locks WHERE name = ? AND holder_id = ? AND token = ?", 
                             (data['name'], data['client_id'], data['token']))
        return (jsonify({"status": "RELEASED"}), 200) if cursor.rowcount > 0 else (jsonify({"status": "FAILED"}), 400)

if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=int(sys.argv[1]) if len(sys.argv) > 1 else 5000)