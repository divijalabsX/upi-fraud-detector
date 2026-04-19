# ============================================================
# model.py — UPI Fraud Detection ML Model
# ============================================================
# Uses Isolation Forest (unsupervised anomaly detection)
# No labeled fraud data needed — it learns "normal" behavior
# and flags anything that looks unusual.
# ============================================================

import numpy as np
import pickle
import os
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler

# ── Feature engineering ──────────────────────────────────────
def extract_features(transaction: dict) -> list:
    """
    Convert a raw transaction dict into a numeric feature vector.

    Features used:
      0  amount          — transaction value in ₹
      1  hour_of_day     — 0–23  (late-night txns are riskier)
      2  is_new_device   — 0 or 1
      3  is_new_location — 0 or 1
      4  txn_per_hour    — how many txns this user sent in last hour
      5  amount_zscore   — how far amount deviates from user's mean
    """
    amount          = float(transaction.get("amount", 0))
    hour            = int(transaction.get("hour_of_day", 12))
    is_new_device   = int(transaction.get("is_new_device", 0))
    is_new_location = int(transaction.get("is_new_location", 0))
    txn_per_hour    = float(transaction.get("txn_per_hour", 1))
    amount_zscore   = float(transaction.get("amount_zscore", 0))

    return [amount, hour, is_new_device, is_new_location,
            txn_per_hour, amount_zscore]


# ── Training data (synthetic but realistic) ──────────────────
def generate_training_data() -> np.ndarray:
    """
    Generate synthetic 'normal' transaction data for training.
    In production you'd replace this with real historical data.
    """
    np.random.seed(42)
    n_normal = 1000

    normal_data = []
    for _ in range(n_normal):
        amount          = np.random.normal(loc=2000,  scale=1500)
        amount          = max(10, amount)                  # no negatives
        hour            = np.random.randint(8, 23)         # daytime mostly
        is_new_device   = np.random.choice([0, 1], p=[0.95, 0.05])
        is_new_location = np.random.choice([0, 1], p=[0.92, 0.08])
        txn_per_hour    = np.random.randint(1, 5)
        amount_zscore   = np.random.normal(0, 0.8)

        normal_data.append([amount, hour, is_new_device,
                            is_new_location, txn_per_hour, amount_zscore])

    return np.array(normal_data)


# ── Model class ───────────────────────────────────────────────
class FraudDetector:
    """
    Wraps Isolation Forest with a StandardScaler.
    Provides:
      .train()   — train on synthetic data
      .predict() — returns risk score + label for one transaction
      .save()    — persist model to disk
      .load()    — restore model from disk
    """

    MODEL_PATH  = "fraud_model.pkl"
    SCALER_PATH = "scaler.pkl"

    def __init__(self):
        self.model  = IsolationForest(
            n_estimators=200,       # more trees = more accurate
            contamination=0.05,     # expect ~5 % fraud in real world
            random_state=42
        )
        self.scaler  = StandardScaler()
        self.trained = False

    # ── Train ──────────────────────────────────────────────────
    def train(self, data: np.ndarray = None):
        if data is None:
            data = generate_training_data()

        X = self.scaler.fit_transform(data)
        self.model.fit(X)
        self.trained = True
        print(f"✅ Model trained on {len(data)} transactions")

    # ── Predict ────────────────────────────────────────────────
    def predict(self, transaction: dict) -> dict:
        """
        Returns a dict:
          {
            "is_fraud": True/False,
            "risk_score": 0.0–1.0,   (higher = riskier)
            "risk_level": "LOW" | "MEDIUM" | "HIGH" | "CRITICAL",
            "reasons": [...]
          }
        """
        if not self.trained:
            self.load()               # try loading from disk

        features = extract_features(transaction)
        X = self.scaler.transform([features])

        # Isolation Forest: -1 = anomaly, +1 = normal
        label = self.model.predict(X)[0]

        # decision_function: more negative = more anomalous
        raw_score = self.model.decision_function(X)[0]
        
                # decision_function: more negative = more anomalous
        raw_score = self.model.decision_function(X)[0]

        # Convert raw anomaly score → usable risk
        risk_score = max(0, -raw_score)

        # 🔥 Rule-based boosts
        if transaction.get("amount", 0) > 20000:
            risk_score += 0.4

        if transaction.get("hour_of_day", 12) < 5:
            risk_score += 0.3

        if transaction.get("is_new_device", 0):
            risk_score += 0.2

        if transaction.get("is_new_location", 0):
            risk_score += 0.2

        if transaction.get("txn_per_hour", 1) > 5:
            risk_score += 0.2

        # Clamp
        risk_score = float(np.clip(risk_score, 0, 1))

        # Determine risk level
        if risk_score >= 0.85:
            risk_level = "CRITICAL"
        elif risk_score >= 0.65:
            risk_level = "HIGH"
        elif risk_score >= 0.40:
            risk_level = "MEDIUM"
        else:
            risk_level = "LOW"

        is_fraud = (label == -1) or (risk_score >= 0.65)

        reasons = self._explain(transaction, risk_score)

        return {
            "is_fraud":   is_fraud,
            "risk_score": round(risk_score, 3),
            "risk_level": risk_level,
            "reasons":    reasons
        }

    # ── Rule-based explanation ─────────────────────────────────
    def _explain(self, txn: dict, score: float) -> list:
        reasons = []
        amount = float(txn.get("amount", 0))
        hour   = int(txn.get("hour_of_day", 12))

        if amount > 20000:
            reasons.append(f"Very large amount (₹{amount:,.0f})")
        elif amount > 10000:
            reasons.append(f"Large amount (₹{amount:,.0f})")

        if hour < 5 or hour > 23:
            reasons.append(f"Unusual hour ({hour}:00)")

        if txn.get("is_new_device"):
            reasons.append("Transaction from new/unknown device")

        if txn.get("is_new_location"):
            reasons.append("Transaction from new location")

        if float(txn.get("txn_per_hour", 1)) > 5:
            reasons.append("Multiple rapid transactions")

        if abs(float(txn.get("amount_zscore", 0))) > 2:
            reasons.append("Amount is unusual for this user")

        if not reasons and score >= 0.40:
            reasons.append("ML model flagged unusual pattern")

        return reasons

    # ── Persist ────────────────────────────────────────────────
    def save(self):
        with open(self.MODEL_PATH,  "wb") as f:
            pickle.dump(self.model,  f)
        with open(self.SCALER_PATH, "wb") as f:
            pickle.dump(self.scaler, f)
        print(f"💾 Model saved → {self.MODEL_PATH}")

    def load(self):
        if os.path.exists(self.MODEL_PATH):
            with open(self.MODEL_PATH,  "rb") as f:
                self.model  = pickle.load(f)
            with open(self.SCALER_PATH, "rb") as f:
                self.scaler = pickle.load(f)
            self.trained = True
            print("📂 Model loaded from disk")
        else:
            print("⚠️  No saved model found — training fresh model")
            self.train()
            self.save()


# ── Quick self-test ───────────────────────────────────────────
if __name__ == "__main__":
    detector = FraudDetector()
    detector.train()
    detector.save()

    test_cases = [
        {"amount": 500,   "hour_of_day": 14, "is_new_device": 0,
         "is_new_location": 0, "txn_per_hour": 1, "amount_zscore": 0.1,
         "description": "Normal grocery payment"},

        {"amount": 49000, "hour_of_day": 3,  "is_new_device": 1,
         "is_new_location": 1, "txn_per_hour": 8, "amount_zscore": 4.2,
         "description": "Suspicious large night transfer"},

        {"amount": 1500,  "hour_of_day": 11, "is_new_device": 0,
         "is_new_location": 0, "txn_per_hour": 2, "amount_zscore": 0.3,
         "description": "Online shopping"},
    ]

    print("\n" + "="*55)
    print("  UPI FRAUD DETECTOR — TEST RESULTS")
    print("="*55)

    for txn in test_cases:
        result = detector.predict(txn)
        icon = "🚨" if result["is_fraud"] else "✅"
        print(f"\n{icon} {txn['description']}")
        print(f"   Risk: {result['risk_level']} ({result['risk_score']:.1%})")
        if result["reasons"]:
            for r in result["reasons"]:
                print(f"   • {r}")
