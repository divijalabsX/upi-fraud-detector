# ============================================================
# alert_agent.py — Smart Alert & Suggestion Engine
# ============================================================
# Generates human-readable alerts and actionable suggestions
# based on the fraud detection result.
# ============================================================

from datetime import datetime


class AlertAgent:
    """
    Takes a transaction + fraud result and produces:
      - A formatted alert message
      - Prioritized action suggestions
      - A severity color code (for UI)
    """

    SEVERITY_CONFIG = {
        "LOW":      {"emoji": "✅", "color": "#22c55e", "label": "Safe"},
        "MEDIUM":   {"emoji": "⚠️",  "color": "#f59e0b", "label": "Caution"},
        "HIGH":     {"emoji": "🚨", "color": "#ef4444", "label": "Suspicious"},
        "CRITICAL": {"emoji": "🔴", "color": "#7f1d1d", "label": "BLOCK NOW"},
    }

    def generate_alert(self, transaction: dict, fraud_result: dict) -> dict:
        """
        Main method. Returns a full alert payload.
        """
        level  = fraud_result.get("risk_level", "LOW")
        config = self.SEVERITY_CONFIG[level]
        amount = transaction.get("amount", 0)
        payee  = transaction.get("payee", "Unknown recipient")
        upi_id = transaction.get("upi_id", "unknown@upi")

        message    = self._build_message(level, amount, payee, upi_id, fraud_result)
        actions    = self._suggest_actions(level, fraud_result)
        tips       = self._safety_tips(fraud_result)
        timestamp  = datetime.now().strftime("%d %b %Y, %I:%M %p")

        return {
            "timestamp":   timestamp,
            "level":       level,
            "emoji":       config["emoji"],
            "color":       config["color"],
            "label":       config["label"],
            "message":     message,
            "actions":     actions,
            "safety_tips": tips,
            "risk_score":  fraud_result.get("risk_score", 0),
            "reasons":     fraud_result.get("reasons", []),
            "should_block": level == "CRITICAL",
        }

    # ── Message builder ───────────────────────────────────────
    def _build_message(self, level, amount, payee, upi_id, result):
        score_pct = int(result.get("risk_score", 0) * 100)

        if level == "CRITICAL":
            return (
                f"🔴 CRITICAL ALERT — DO NOT PROCEED!\n"
                f"Transaction of ₹{amount:,.0f} to {payee} ({upi_id})\n"
                f"Risk Score: {score_pct}% — This transaction looks like FRAUD."
            )
        elif level == "HIGH":
            return (
                f"🚨 HIGH RISK Transaction Detected!\n"
                f"₹{amount:,.0f} → {payee} ({upi_id})\n"
                f"Risk Score: {score_pct}% — Please verify before proceeding."
            )
        elif level == "MEDIUM":
            return (
                f"⚠️ Suspicious Transaction — Proceed with caution\n"
                f"₹{amount:,.0f} → {payee}\n"
                f"Risk Score: {score_pct}% — Double-check the recipient."
            )
        else:
            return (
                f"✅ Transaction Looks Safe\n"
                f"₹{amount:,.0f} → {payee}\n"
                f"Risk Score: {score_pct}% — No unusual patterns found."
            )

    # ── Action suggestions ────────────────────────────────────
    def _suggest_actions(self, level: str, result: dict) -> list:
        base_actions = {
            "LOW": [
                "✅ You may proceed with this transaction",
                "📋 Keep the payment receipt",
            ],
            "MEDIUM": [
                "🔍 Verify the UPI ID with the recipient directly",
                "📞 Call the recipient on a known phone number",
                "💬 Do not share OTP with anyone",
                "⏸️  Pause and double-check before paying",
            ],
            "HIGH": [
                "⛔ STOP — Do not pay yet",
                "📞 Call your bank helpline immediately",
                "🔒 Lock your UPI PIN temporarily",
                "🕵️ Report this UPI ID to NPCI: 1800-120-1740",
                "📷 Take a screenshot as evidence",
            ],
            "CRITICAL": [
                "🚫 DO NOT PROCEED WITH THIS TRANSACTION",
                "📵 Close the UPI app immediately",
                "🏦 Call your bank to BLOCK your account",
                "🔑 Change your UPI PIN RIGHT NOW",
                "🚔 File a complaint: cybercrime.gov.in",
                "📞 National Cyber Crime Helpline: 1930",
            ],
        }
        return base_actions.get(level, [])

    # ── Safety tips ───────────────────────────────────────────
    def _safety_tips(self, result: dict) -> list:
        tips = []
        reasons = result.get("reasons", [])

        if any("device" in r.lower() for r in reasons):
            tips.append("💡 Always verify transactions on trusted devices only")

        if any("night" in r.lower() or "hour" in r.lower() for r in reasons):
            tips.append("💡 Be extra careful with transactions late at night")

        if any("large" in r.lower() or "₹" in r for r in reasons):
            tips.append("💡 For large transfers, always confirm via call first")

        if any("rapid" in r.lower() or "multiple" in r.lower() for r in reasons):
            tips.append("💡 Multiple rapid transactions may indicate account takeover")

        if not tips:
            tips.append("💡 Always verify UPI IDs before sending money")

        return tips


# ── CLI demo ──────────────────────────────────────────────────
if __name__ == "__main__":
    from model import FraudDetector

    detector = FraudDetector()
    detector.train()

    agent = AlertAgent()

    test_transactions = [
        {
            "amount": 500, "payee": "Raju Kirana Store",
            "upi_id": "rajukirana@paytm", "hour_of_day": 11,
            "is_new_device": 0, "is_new_location": 0,
            "txn_per_hour": 1, "amount_zscore": 0.1
        },
        {
            "amount": 49000, "payee": "Unknown Person",
            "upi_id": "win.prize99@ybl", "hour_of_day": 3,
            "is_new_device": 1, "is_new_location": 1,
            "txn_per_hour": 9, "amount_zscore": 5.1
        },
    ]

    print("\n" + "="*60)
    print("  SMART ALERT AGENT — DEMO OUTPUT")
    print("="*60)

    for txn in test_transactions:
        result = detector.predict(txn)
        alert  = agent.generate_alert(txn, result)

        print(f"\n{alert['emoji']} [{alert['label']}] — {alert['timestamp']}")
        print(f"  {alert['message']}")
        print(f"\n  📋 Recommended Actions:")
        for action in alert["actions"]:
            print(f"    {action}")
        if alert["safety_tips"]:
            print(f"\n  💡 Safety Tips:")
            for tip in alert["safety_tips"]:
                print(f"    {tip}")
        print("-"*60)
