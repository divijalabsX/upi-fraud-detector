# UPI Fraud Detector
### Hybrid Anomaly Detection & Transaction Risk Assessment System

A machine learning-powered system designed to identify potentially suspicious UPI transactions using unsupervised anomaly detection, behavioural transaction features, and rule-based risk assessment.

The system analyzes transaction characteristics, calculates a risk score, classifies transactions into different severity levels, and provides an interface for monitoring transaction activity.

---

## 1. Problem Statement

UPI has made digital payments fast and convenient, but the increasing volume of digital transactions also creates opportunities for fraudulent activities.

Traditional transaction monitoring systems often rely on predefined rules and fixed thresholds. Such approaches may struggle to identify unusual behavioural patterns that do not match previously defined fraud scenarios.

This project explores a hybrid approach that combines machine learning-based anomaly detection with rule-based risk assessment to identify potentially suspicious transactions.

### Project Objectives

- Detect unusual transaction patterns using unsupervised machine learning.
- Analyze behavioural indicators associated with suspicious transactions.
- Generate an interpretable risk score for every analyzed transaction.
- Classify transactions into LOW, MEDIUM, HIGH, and CRITICAL risk levels.
- Provide actionable recommendations based on the detected risk.
- Maintain transaction history and provide monitoring capabilities through a dashboard.

---

## 2. System Overview

The application follows a client-server architecture.

The Streamlit dashboard communicates with a Flask REST API, which processes transaction information and passes the extracted features to the hybrid fraud detection engine.

The detection engine combines Isolation Forest anomaly detection with rule-based scoring to produce a final risk assessment.

Transaction results are subsequently stored for historical monitoring and dashboard analytics.

### Core Features

**Hybrid Fraud Detection**
- Isolation Forest-based anomaly detection.
- Rule-based transaction risk assessment.
- Combined risk scoring mechanism.

**Behavioural Feature Analysis**
- Transaction amount.
- Time of transaction.
- Device familiarity.
- Location familiarity.
- Transaction frequency.
- Spending deviation from historical behaviour.

**Risk Classification**
- LOW
- MEDIUM
- HIGH
- CRITICAL

**Transaction Monitoring**
- Transaction history.
- Risk classification.
- Flagged transaction count.
- Transaction volume statistics.

**Backend API**
- REST-based transaction analysis.
- Input validation.
- Health monitoring.
- Transaction history retrieval.
- Summary statistics.

**Interactive Dashboard**
- Transaction analysis interface.
- Risk score visualization.
- Transaction history.
- Monitoring statistics.

---

## 3. Architecture

The system consists of five primary components:

1. User Interface
2. Flask API
3. Feature Extraction
4. Hybrid Fraud Detection Engine
5. Transaction Logging and Monitoring

### Transaction Processing Workflow

1. The user enters transaction details through the dashboard.
2. The dashboard sends a JSON request to the Flask API.
3. The API validates and normalizes the transaction information.
4. The feature extraction module converts transaction information into a numerical feature vector.
5. StandardScaler transforms the features.
6. Isolation Forest identifies anomalous transaction patterns.
7. The rule-based engine evaluates predefined suspicious transaction conditions.
8. The hybrid scoring mechanism calculates the final risk score.
9. The transaction is classified into a risk category.
10. The result is returned to the dashboard and stored in the transaction history.

---

## 4. Machine Learning Approach

### Isolation Forest

The project uses Isolation Forest, an unsupervised anomaly detection algorithm.

Unlike conventional supervised classification algorithms, Isolation Forest does not require labelled fraud examples during its initial training process.

Instead, it learns the distribution of normal transaction behaviour and identifies observations that deviate from the learned patterns.

### Model Configuration

| Parameter | Value |
|---|---|
| Algorithm | Isolation Forest |
| Number of estimators | 200 |
| Contamination | 0.05 |
| Random state | 42 |
| Training samples | 1,000 |
| Training data | Synthetic normal transactions |

### Feature Engineering

The model currently uses six transaction features.

| Feature | Description |
|---|---|
| amount | Transaction amount |
| hour_of_day | Hour of transaction |
| is_new_device | Indicates an unfamiliar device |
| is_new_location | Indicates an unfamiliar location |
| txn_per_hour | Number of transactions per hour |
| amount_zscore | Deviation from the user's average transaction amount |

StandardScaler is used to standardize the numerical features before model training and inference.

### Hybrid Risk Scoring

The system combines two sources of risk information:

**1. Machine Learning Score**

Derived from the Isolation Forest decision function.

**2. Rule-Based Score**

Increases when predefined suspicious transaction conditions are satisfied.

The final risk score is calculated as:

`Risk Score = max(Rule Score, 0.7 × ML Score)`

The score is constrained between 0 and 1.

### Risk Classification

| Risk Score | Risk Level |
|---|---|
| 0.00–0.39 | LOW |
| 0.40–0.64 | MEDIUM |
| 0.65–0.84 | HIGH |
| 0.85–1.00 | CRITICAL |

The system also generates a binary fraud flag based on the anomaly detection result or a high-risk threshold.

---

## 5. Technology Stack

| Category | Technologies |
|---|---|
| Programming Language | Python |
| Machine Learning | Scikit-learn |
| Numerical Processing | NumPy |
| Feature Scaling | StandardScaler |
| Anomaly Detection | Isolation Forest |
| Backend | Flask |
| API Communication | REST API, JSON |
| Frontend | Streamlit |
| Data Storage | JSON |
| Model Persistence | Pickle |
| Deployment | Render |
| Version Control | Git, GitHub |

---

## 6. Project Structure

```text
upi-fraud-detector/
│
├── backend/
│   ├── app.py
│   ├── model.py
│   ├── alert_agent.py
│   └── transaction_logger.py
│
├── dashboard/
│   └── streamlit_app.py
│
├── data/
│   └── transaction_log.json
│
├── fraud_model.pkl
├── scaler.pkl
│
├── requirements.txt
├── README.md
└── .gitignore
```

Note: Runtime transaction logs should be generated locally and excluded from version control. The structure above represents the main application components.

---

## 7. API Endpoints

The Flask backend exposes the following endpoints:

| Method | Endpoint | Description |
|---|---|---|
| GET | `/` | API information |
| POST | `/analyze` | Analyze a transaction |
| GET | `/history` | Retrieve transaction history |
| GET | `/stats` | Retrieve transaction statistics |
| GET | `/health` | Check backend availability |

### Example Transaction Request

```json
{
  "user_id": "user_001",
  "amount": 49000,
  "payee": "Unknown Person",
  "upi_id": "unknown@ybl",
  "hour_of_day": 3,
  "is_new_device": 1,
  "is_new_location": 1,
  "txn_per_hour": 9,
  "amount_zscore": 5.1
}
```

### Example Response

```json
{
  "status": "analyzed",
  "fraud_result": {
    "is_fraud": true,
    "risk_score": 1.0,
    "risk_level": "CRITICAL",
    "reasons": [
      "Very large amount",
      "Unusual hour",
      "Transaction from new/unknown device",
      "Transaction from new location",
      "Multiple rapid transactions",
      "Amount is unusual for this user"
    ]
  }
}
```

The example illustrates the response structure. Actual risk scores and explanations depend on the model and supplied transaction features.

---

## 8. Installation and Execution

### Prerequisites

- Python 3.11
- Git
- pip

### Step 1: Clone the repository

```bash
git clone https://github.com/divijalabsX/upi-fraud-detector.git

cd upi-fraud-detector
```

### Step 2: Create a virtual environment

```bash
python -m venv .venv
```

Activate it on Windows:

```powershell
.venv\Scripts\activate
```

### Step 3: Install dependencies

```bash
pip install -r requirements.txt
```

### Step 4: Start the backend

Open a terminal:

```bash
cd backend

python app.py
```

The Flask API starts at:

`http://127.0.0.1:5000`

### Step 5: Start the dashboard

Open another terminal from the project root:

```bash
streamlit run dashboard/streamlit_app.py
```

The dashboard becomes available at:

`http://localhost:8501`

---

## 9. Limitations

The current implementation is an educational prototype.

- The model is trained on synthetically generated normal transactions.
- The model has not been validated against a representative, independently labelled UPI fraud dataset.
- Anomaly detection does not automatically establish that a transaction is fraudulent.
- Historical transaction features are not yet automatically integrated into the API prediction workflow.
- JSON-based storage is intended for prototype-scale usage.
- The system is not connected to actual UPI payment infrastructure.
- The system does not independently block or reverse financial transactions.

Consequently, the current risk scores should not be interpreted as calibrated probabilities of fraud.

---

## 10. Future Improvements

- Integrate labelled transaction datasets for supervised evaluation.
- Compare Isolation Forest against alternative anomaly detection algorithms.
- Integrate historical behavioural features into the prediction pipeline.
- Improve risk score calibration.
- Integrate the alert engine into the main API workflow.
- Implement automated unit and integration testing.
- Introduce persistent database storage.
- Add model monitoring and data drift detection.
- Improve explainability and transaction-level auditability.
- Explore real-time transaction monitoring integrations.

---

## 11. Disclaimer

This project is developed for educational and research purposes.

It uses synthetic training data and is not connected to real UPI infrastructure. Its predictions are experimental and should not be used as the sole basis for actual financial decisions.

---

## Author

**Divija Jain**

Computer Science Engineering | AI & ML

GitHub: https://github.com/divijalabsX
