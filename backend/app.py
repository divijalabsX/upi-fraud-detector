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

# ── Home route ───────────────────────────────────────────────
@app.route("/")
def home():
    return {
        "message": "UPI Fraud Detection API is live 🚀",
        "endpoints": ["/health", "/analyze"]
    }

# ── Endpoint 1: Analyze a transaction ─────────────────────────
from flask import request, jsonify

@app.route('/analyze', methods=['POST'])
def analyze():
    try:
        data = request.get_json(silent=True)

        if not isinstance(data, dict):
            return jsonify({
                "error": "A valid JSON object is required."
            }), 400

        # Validate required transaction input
        if "amount" not in data:
            return jsonify({
                "error": "Missing required field: amount"
            }), 400

        # Extract and normalize transaction fields
        txn = {
            "user_id": str(data.get("user_id", "anonymous")),
            "amount": float(data["amount"]),
            "hour_of_day": int(data.get("hour_of_day", 12)),
            "is_new_device": int(data.get("is_new_device", 0)),
            "is_new_location": int(data.get("is_new_location", 0)),
            "txn_per_hour": int(data.get("txn_per_hour", 1)),
            "amount_zscore": float(data.get("amount_zscore", 0.0)),
            "payee": str(data.get("payee", data.get("payee_name", "Unknown"))),
            "upi_id": str(data.get("upi_id", "unknown@upi")),
        }

        # Basic input validation
        if txn["amount"] < 0:
            return jsonify({
                "error": "Amount cannot be negative."
            }), 400

        if not 0 <= txn["hour_of_day"] <= 23:
            return jsonify({
                "error": "hour_of_day must be between 0 and 23."
            }), 400

        for field in ("is_new_device", "is_new_location"):
            if txn[field] not in (0, 1):
                return jsonify({
                    "error": f"{field} must be 0 or 1."
                }), 400

        if txn["txn_per_hour"] < 1:
            return jsonify({
                "error": "txn_per_hour must be at least 1."
            }), 400

        # Use supplied features for this prototype.
        # Do not silently overwrite the input with historical features
        # until feature computation is deliberately integrated.
        fraud_result = detector.predict(txn)

        # Normalize the detector response for JSON serialization
        fraud_result = {
            "is_fraud": bool(fraud_result["is_fraud"]),
            "risk_score": float(fraud_result["risk_score"]),
            "risk_level": str(fraud_result["risk_level"]),
            "reasons": [
                str(reason)
                for reason in fraud_result.get("reasons", [])
            ]
        }

        # Save the transaction before returning success
        save_transaction(txn, fraud_result)

        return jsonify({
            "status": "analyzed",
            "transaction": txn,
            "fraud_result": fraud_result
        }), 200

    except (TypeError, ValueError) as e:
        return jsonify({
            "error": f"Invalid transaction input: {str(e)}"
        }), 400

    except Exception:
        app.logger.exception("Transaction analysis failed")
        return jsonify({
            "error": "Transaction analysis failed. Check backend logs."
        }), 500


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
