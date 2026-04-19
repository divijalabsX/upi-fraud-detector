# ============================================================
# streamlit_app.py — Web Dashboard UI
# ============================================================
# Run with:  streamlit run dashboard/streamlit_app.py
# ============================================================

import streamlit as st
import requests
import json
from datetime import datetime

# ── Page config ───────────────────────────────────────────────
st.set_page_config(
    page_title="UPI Fraud Detector",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

API_URL = "http://localhost:5000"

# ── Custom CSS ────────────────────────────────────────────────
st.markdown("""
<style>
    .main { background: #0f172a; }
    .stApp { background: #0f172a; color: #e2e8f0; }
    .metric-card {
        background: #1e293b;
        border: 1px solid #334155;
        border-radius: 12px;
        padding: 20px;
        text-align: center;
    }
    .alert-critical { border-left: 4px solid #dc2626; background: #1c0a0a; padding: 16px; border-radius: 8px; }
    .alert-high     { border-left: 4px solid #ef4444; background: #1c1010; padding: 16px; border-radius: 8px; }
    .alert-medium   { border-left: 4px solid #f59e0b; background: #1c1800; padding: 16px; border-radius: 8px; }
    .alert-low      { border-left: 4px solid #22c55e; background: #0a1c0e; padding: 16px; border-radius: 8px; }
</style>
""", unsafe_allow_html=True)

# ── Sidebar ───────────────────────────────────────────────────
with st.sidebar:
    st.image("https://img.icons8.com/fluency/96/shield.png", width=80)
    st.title("🛡️ UPI Fraud\nDetector")
    st.markdown("---")
    st.markdown("**API Status**")

    try:
        r = requests.get(f"{API_URL}/health", timeout=2)
        if r.status_code == 200:
            st.success("🟢 API Online")
        else:
            st.error("🔴 API Error")
    except:
        st.error("🔴 API Offline\nStart: `python app.py`")

    st.markdown("---")
    page = st.radio("Navigate", ["🔍 Check Transaction", "📊 Dashboard", "📋 History"])


# ═══════════════════════════════════════════════════════════════
# PAGE 1 — CHECK TRANSACTION
# ═══════════════════════════════════════════════════════════════
if "Check" in page:
    st.title("🔍 Check a Transaction")
    st.markdown("Enter transaction details below to check if it's suspicious.")

    col1, col2 = st.columns(2)

    with col1:
        user_id = st.text_input("👤 User ID", value="user_001")
        amount  = st.number_input("💰 Amount (₹)", min_value=1, value=1000, step=100)
        payee   = st.text_input("🏪 Payee Name", value="Local Shop")
        upi_id  = st.text_input("📱 UPI ID", value="shop@okaxis")

    with col2:
        hour      = st.slider("🕐 Hour of Day", 0, 23, datetime.now().hour)
        new_dev   = st.checkbox("📱 New/Unknown Device")
        new_loc   = st.checkbox("📍 New Location")
        st.markdown("")
        st.markdown("")

    st.markdown("---")
    check_btn = st.button("🔍 ANALYZE TRANSACTION", use_container_width=True, type="primary")

    if check_btn:
        payload = {
            "user_id":         user_id,
            "amount":          amount,
            "payee":           payee,
            "upi_id":          upi_id,
            "hour_of_day":     hour,
            "is_new_device":   int(new_dev),
            "is_new_location": int(new_loc),
        }

        with st.spinner("🤖 AI is analyzing..."):
            try:
                r = requests.post(f"{API_URL}/analyze", json=payload, timeout=10)
                data = r.json()
            except Exception as e:
                st.error(f"❌ Could not reach API: {e}")
                st.stop()

        level = data.get("risk_level", "LOW")
        score = int(data.get("risk_score", 0) * 100)
        reasons = data.get("reasons", [])

        css_class = f"alert-{level.lower()}"

        emoji_map = {
             "LOW": "✅",
             "MEDIUM": "⚠️",
             "HIGH": "🚨",
             "CRITICAL": "🔴"
        }

        emoji = emoji_map.get(level, "✅")
        label = level

        st.markdown(f"""
        <div class="{css_class}">
            <h2>{emoji} {label} — Risk Score: {score}%</h2>
            <p>Risk level detected based on transaction pattern.</p>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("### 📋 Recommended Actions")
        for reason in reasons:
                st.markdown(f"- {reason}")

# ═══════════════════════════════════════════════════════════════
# PAGE 2 — DASHBOARD
# ═══════════════════════════════════════════════════════════════
elif "Dashboard" in page:
    st.title("📊 Fraud Detection Dashboard")

    try:
        stats = requests.get(f"{API_URL}/stats", timeout=3).json()
    except:
        st.error("Cannot load stats — is the API running?")
        st.stop()

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("Total Transactions", stats.get("total", 0))
    with c2:
        st.metric("🚨 Flagged", stats.get("flagged", 0))
    with c3:
        st.metric("✅ Safe", stats.get("safe", 0))
    with c4:
        st.metric("Flag Rate", f"{stats.get('flag_rate', 0)}%")

    st.markdown("---")
    st.markdown("#### 💳 Total Amount Processed")
    total_amt = stats.get("total_amount", 0)
    st.markdown(f"## ₹{total_amt:,.0f}")


# ═══════════════════════════════════════════════════════════════
# PAGE 3 — HISTORY
# ═══════════════════════════════════════════════════════════════
elif "History" in page:
    st.title("📋 Transaction History")

    try:
        data    = requests.get(f"{API_URL}/history?limit=100", timeout=3).json()
        records = data.get("records", [])
    except:
        st.error("Cannot load history — is the API running?")
        st.stop()

    if not records:
        st.info("No transactions analyzed yet. Go to 'Check Transaction' to start!")
    else:
        for rec in records:
            result = rec.get("fraud_result", {})
            level  = result.get("risk_level", "LOW")
            icon   = {"LOW": "✅", "MEDIUM": "⚠️", "HIGH": "🚨", "CRITICAL": "🔴"}.get(level, "✅")
            label  = f"{icon} ₹{rec.get('amount', '?'):,} → {rec.get('payee', '?')} — {level}"
            with st.expander(label):
                st.json(rec)
