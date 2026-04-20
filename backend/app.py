# ============================================================
# app.py — Flask REST API Server
# ============================================================
# This is the BRAIN of the system.
# The Android app and Streamlit dashboard both talk to this.
#
# Endpoints:
#   POST /analyze      ← send a transaction, get fraud verdict
#   GET  /history      ← get all logged transactions
#   GET  /stats        ← summary statistics
#   GET  /health       ← server health check
# ============================================================

from flask import Flask, request, jsonify
from flask_cors import CORS
from model import FraudDetector
from alert_agent import AlertAgent
from transaction_logger import (
    save_transaction, load_all_transactions,
    compute_user_stats, get_summary_stats
)
import datetime

app = Flask(__name__)
CORS(app)   # Allow requests from Android app / dashboard

# ── Load model once on startup ────────────────────────────────
detector = FraudDetector()
detector.load()          # loads from disk, trains fresh if not found
agent    = AlertAgent()

print("🚀 UPI Fraud Detection API is running!")
print("   Endpoints: /analyze  /history  /stats  /health")


# ── Endpoint 1: Analyze a transaction ─────────────────────────
from flask import request, jsonify

@app.route('/analyze', methods=['POST'])
def analyze():
    try:
        data = request.get_json()

        if not data:
            return jsonify({"error": "No JSON received"}), 400

        # Extract fields safely
        txn = {
            "amount": data.get("amount", 0),
            "hour_of_day": data.get("hour_of_day", 12),
            "is_new_device": data.get("is_new_device", 0),
            "is_new_location": data.get("is_new_location", 0),
            "txn_per_hour": data.get("txn_per_hour", 1),
            "amount_zscore": data.get("amount_zscore", 0.0),
            "description": data.get("description", "unknown")
        }

        result = detector.predict(txn)

        return jsonify(result)

    except Exception as e:
        return jsonify({"error": str(e)})
    
    # ── Enrich with live user stats ───────────────────────────
    user_stats = compute_user_stats(
        data["user_id"], float(data["amount"])
    )
    data.update(user_stats)

    # ── Default missing fields ────────────────────────────────
    data.setdefault("hour_of_day",     datetime.datetime.now().hour)
    data.setdefault("is_new_device",   0)
    data.setdefault("is_new_location", 0)
    data.setdefault("payee",           "Unknown")
    data.setdefault("upi_id",          "unknown@upi")

    # ── Run detection ─────────────────────────────────────────
    fraud_result = detector.predict(data)
    alert        = agent.generate_alert(data, fraud_result)

    # ── Log the transaction ───────────────────────────────────
    save_transaction(data, fraud_result)

    # ── Respond ───────────────────────────────────────────────
    return jsonify({
        "status":       "analyzed",
        "transaction":  data,
        "fraud_result": fraud_result,
        "alert":        alert,
    }), 200


# ── Endpoint 2: Transaction history ───────────────────────────
@app.route("/history", methods=["GET"])
def history():
    limit  = int(request.args.get("limit", 50))
    records = load_all_transactions()
    return jsonify({
        "count":   len(records),
        "records": records[-limit:][::-1]   # newest first
    }), 200


# ── Endpoint 3: Summary stats ─────────────────────────────────
@app.route("/stats", methods=["GET"])
def stats():
    return jsonify(get_summary_stats()), 200


# ── Endpoint 4: Health check ──────────────────────────────────
@app.route("/health", methods=["GET"])
def health():
    return jsonify({
        "status":  "ok",
        "model":   "IsolationForest v1",
        "time":    datetime.datetime.now().isoformat()
    }), 200


# ── Run ───────────────────────────────────────────────────────
if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

# ── Homepage ───────────────────────────────────────────────────
@app.route("/")
def home():
    return {
        "message": "UPI Fraud Detection API is live 🚀",
        "endpoints": ["/health", "/analyze"]
    }