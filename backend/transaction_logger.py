# ============================================================
# transaction_logger.py — Log & Load Transactions
# ============================================================
# Saves all analyzed transactions to a local JSON file.
# Also computes user-level statistics used as features.
# ============================================================

import json
import os
from datetime import datetime
from collections import defaultdict

LOG_FILE = "data/transaction_log.json"


def ensure_data_dir():
    os.makedirs("data", exist_ok=True)


def load_all_transactions() -> list:
    ensure_data_dir()
    if not os.path.exists(LOG_FILE):
        return []
    with open(LOG_FILE, "r") as f:
        return json.load(f)


def save_transaction(transaction: dict, result: dict):
    """Append a transaction + its fraud result to the log."""
    ensure_data_dir()
    records = load_all_transactions()

    record = {
        **transaction,
        "fraud_result": result,
        "logged_at": datetime.now().isoformat(),
    }
    records.append(record)

    with open(LOG_FILE, "w") as f:
        json.dump(records, f, indent=2)


def compute_user_stats(user_id: str, amount: float) -> dict:
    """
    Compute live features for a user based on their history:
      - amount_zscore: how unusual is this amount for this user?
      - txn_per_hour:  how many txns did they do in the last hour?
    """
    records = load_all_transactions()
    user_txns = [r for r in records if r.get("user_id") == user_id]

    if not user_txns:
        return {"amount_zscore": 0.0, "txn_per_hour": 1}

    amounts = [float(r["amount"]) for r in user_txns]
    mean_amt = sum(amounts) / len(amounts)
    std_amt  = (sum((a - mean_amt)**2 for a in amounts) / len(amounts)) ** 0.5
    zscore   = (amount - mean_amt) / (std_amt + 1e-9)

    # Count txns in last 60 minutes
    now = datetime.now()
    recent = [
        r for r in user_txns
        if (now - datetime.fromisoformat(r["logged_at"])).seconds < 3600
    ]

    return {
        "amount_zscore": round(zscore, 3),
        "txn_per_hour":  len(recent) + 1,
    }


def get_summary_stats() -> dict:
    """Return dashboard-level summary stats."""
    records = load_all_transactions()
    if not records:
        return {"total": 0, "flagged": 0, "safe": 0, "total_amount": 0}

    flagged = [r for r in records if r.get("fraud_result", {}).get("is_fraud")]
    total_amount = sum(float(r.get("amount", 0)) for r in records)

    return {
        "total":        len(records),
        "flagged":      len(flagged),
        "safe":         len(records) - len(flagged),
        "total_amount": total_amount,
        "flag_rate":    round(len(flagged) / len(records) * 100, 1),
    }
