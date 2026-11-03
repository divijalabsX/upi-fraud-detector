# ============================================================
# transaction_logger.py - Log & Load Transactions
# ============================================================

import json
import os
import tempfile
import threading

from pathlib import Path
from datetime import datetime
from collections import defaultdict


# Absolute project-relative storage location
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
LOG_FILE = DATA_DIR / "transaction_log.json"

# Protect read-modify-write operations within this process
_log_lock = threading.RLock()


def ensure_data_dir():
    DATA_DIR.mkdir(parents=True, exist_ok=True)


def load_all_transactions() -> list:
    ensure_data_dir()

    if not LOG_FILE.exists():
        return []

    with LOG_FILE.open("r", encoding="utf-8") as f:
        records = json.load(f)

    if not isinstance(records, list):
        raise ValueError("Transaction log must contain a JSON list.")

    return records


def _atomic_write(records: list):
    """
    Write records to a temporary file and atomically replace
    the transaction log.
    """
    ensure_data_dir()

    temp_path = None

    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=DATA_DIR,
            suffix=".tmp",
            delete=False
        ) as f:
            temp_path = Path(f.name)

            json.dump(
                records,
                f,
                indent=2,
                ensure_ascii=False,
                allow_nan=False
            )

            f.flush()
            os.fsync(f.fileno())

        os.replace(temp_path, LOG_FILE)

    finally:
        if temp_path and temp_path.exists():
            temp_path.unlink(missing_ok=True)


def save_transaction(transaction: dict, result: dict):
    """Append a transaction and its fraud result to the log."""

    record = {
        **transaction,
        "fraud_result": result,
        "logged_at": datetime.now().isoformat(),
    }

    with _log_lock:
        records = load_all_transactions()
        records.append(record)
        _atomic_write(records)


def compute_user_stats(user_id: str, amount: float) -> dict:
    """
    Compute user-level transaction features.

    amount_zscore:
        Amount deviation relative to historical amounts.

    txn_per_hour:
        Approximate transaction count in the preceding hour.
    """

    with _log_lock:
        records = load_all_transactions()

    user_txns = [
        r for r in records
        if r.get("user_id") == user_id
    ]

    if not user_txns:
        return {
            "amount_zscore": 0.0,
            "txn_per_hour": 1
        }

    amounts = [
        float(r["amount"])
        for r in user_txns
        if r.get("amount") is not None
    ]

    if not amounts:
        return {
            "amount_zscore": 0.0,
            "txn_per_hour": 1
        }

    mean_amt = sum(amounts) / len(amounts)

    variance = sum(
        (a - mean_amt) ** 2 for a in amounts
    ) / len(amounts)

    std_amt = variance ** 0.5

    # Avoid extreme values for constant/nearly constant history
    if std_amt < 1e-6:
        zscore = 0.0
    else:
        zscore = (amount - mean_amt) / std_amt

    now = datetime.now()

    recent = []

    for r in user_txns:
        logged_at = r.get("logged_at")

        if not logged_at:
            continue

        try:
            txn_time = datetime.fromisoformat(logged_at)

            age_seconds = (now - txn_time).total_seconds()

            if 0 <= age_seconds < 3600:
                recent.append(r)

        except (ValueError, TypeError):
            continue

    return {
        "amount_zscore": round(zscore, 3),
        "txn_per_hour": len(recent) + 1
    }


def get_summary_stats() -> dict:
    """Return dashboard-level summary statistics."""

    with _log_lock:
        records = load_all_transactions()

    if not records:
        return {
            "total": 0,
            "flagged": 0,
            "safe": 0,
            "total_amount": 0,
            "flag_rate": 0
        }

    flagged = [
        r for r in records
        if r.get("fraud_result", {}).get("is_fraud")
    ]

    total_amount = sum(
        float(r.get("amount", 0))
        for r in records
    )

    return {
        "total": len(records),
        "flagged": len(flagged),
        "safe": len(records) - len(flagged),
        "total_amount": total_amount,
        "flag_rate": round(
            len(flagged) / len(records) * 100,
            1
        )
    }