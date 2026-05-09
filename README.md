# UPI Fraud Detector
ML-powered fraud detection system for detecting suspicious UPI transactions using anomaly detection, rule-based scoring, and real-time monitoring.

# Current Features
* ML-based fraud detection using Isolation Forest
* Real-time risk scoring
* Risk levels:
  * LOW
  * MEDIUM
  * HIGH
  * CRITICAL
* Rule-based fraud analysis
* Transaction history logging
* Flask API backend
* Streamlit dashboard UI
* Local + Render deployment support
* REST API endpoints

#  Tech Stack
# Backend
* Python
* Flask
* Scikit-learn
* NumPy
* Pandas

# Frontend
* Streamlit

# Deployment
* Render
* Github

#  Project Structure

backend/
 ── app.py
 ── model.py
 ── alert_agent.py
 ── transaction_logger.py

dashboard/
 ── streamlit_app.py

 | fraud_model.pkl
 | scaler.pkl
 | requirements.txt
 | README.md

# Example Risk Factors
* Large transaction amount
* Late-night transactions
* New/unknown device
* New location
* High transaction frequency
  
# Near Future Planned Upgrades
* Better ML model calibration
* Improved fraud explainability
* Interactive analytics dashboard
* Better UI/UX
* Real transaction dataset training

#  Deployment
* Backend deployed on Render.
* Frontend runs using Streamlit.

# Author
Divija Jain
CSE (AI/ML) Student | ML & AI Projects
