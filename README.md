# Radiation Monitoring Anomaly Detection System

**Bachelor’s thesis project:** Radiation Level Monitoring System with Traditionally Trained Machine Learning Models and a Decision Support Framework Developed Using Generative Artificial Intelligence

This project is a prototype web application for monitoring radiation measurements and detecting anomalous values in time-series data. It was developed as part of my Bachelor’s thesis.

The application works with CSV and ZIP datasets. Imported data is stored in PostgreSQL, cleaned, transformed into features and then used for anomaly detection and model comparison. The current version is file-based, while real-time data processing is planned as a future extension.

The machine learning part of the project is based on traditional machine learning models. The models are trained with standard Python libraries and evaluated with standard classification metrics.

This is an academic prototype and should not be treated as a certified radiation safety system.

## Project idea

The goal of the project is to connect data import, database storage, machine learning and dashboard visualization in one system.

The system supports two types of datasets:

- datasets with an `is_anomaly` column
- datasets without anomaly labels

If labels exist, they are used for model evaluation. If labels do not exist, the system still detects unusual measurements, but it does not calculate supervised metrics such as accuracy, precision or recall.

## Data flow

```text
CSV / ZIP file
      ↓
raw_measurements
      ↓
clean_measurements
      ↓
feature_measurements
      ↓
anomaly_results
      ↓
model_metrics
      ↓
dashboard and reports
```

## Main features

- CSV and ZIP dataset import
- PostgreSQL database storage
- raw, clean and feature data layers
- supervised and unsupervised ML models
- anomaly detection and anomaly score calculation
- model comparison with standard metrics
- dashboard with charts, alerts and anomaly log
- generated tables, reports and plots for evaluation

## Technology stack

**Frontend:** Vue 3, TypeScript, Vite, Chart.js, Pinia  
**Backend:** Python, FastAPI, Uvicorn  
**Database:** PostgreSQL, SQL views  
**Machine learning:** pandas, NumPy, scikit-learn, PyOD

## Database tables

| Table | Purpose |
|---|---|
| `datasets` | information about imported datasets |
| `raw_measurements` | original uploaded measurement rows |
| `clean_measurements` | cleaned and standardized measurements |
| `feature_measurements` | features prepared for ML models |
| `anomaly_results` | model predictions and anomaly scores |
| `model_metrics` | evaluation metrics for each model |
| `app_settings` | active dataset, selected model and threshold |

## Machine learning

The ML workflow includes data cleaning, feature creation, chronological train/test split, model training, prediction and metric calculation.

Because the data is a time series, the split is chronological:

```text
first 70% of records -> training data
last 30% of records  -> test data
```

### Unsupervised models

These models are used because real measurement data may not contain prepared anomaly labels.

| Model | Short description |
|---|---|
| Isolation Forest | isolates unusual records |
| Local Outlier Factor | checks local neighbourhood density |
| One-Class SVM | learns the boundary of normal data |
| DBSCAN | marks low-density points as noise |
| K-Means Distance | uses distance from cluster centers |
| Gaussian Mixture Model | uses probability under learned distributions |
| PCA Reconstruction Error | uses reconstruction error |
| HBOS | histogram-based outlier model |
| ECOD | distribution-based outlier model |

### Supervised models

These models are used only when the dataset contains original labels.

| Model | Short description |
|---|---|
| Logistic Regression | simple baseline classifier |
| Decision Tree | interpretable classification model |
| Random Forest | ensemble classifier |
| Gradient Boosting | boosting-based ensemble model |
| KNN Classifier | distance-based classifier |

## Evaluation

For labeled datasets, the models are evaluated with classification metrics:

- accuracy
- precision
- recall
- F1-score
- ROC-AUC and PR-AUC
- FPR and FNR
- confusion matrix values
- training and prediction time

For unlabeled datasets, the system reports detected anomalies, anomaly rate and anomaly score statistics.

Generated evaluation files are stored in:

```text
ml/outputs/tables/
ml/outputs/figures/
ml/outputs/reports/
```

## Project structure

```text
backend/      FastAPI backend and services
frontend/     Vue application
database/     schema, seed data and SQL views
ml/           model training, scripts and outputs
docs/         additional project documentation
```

## Running the project

Start PostgreSQL:

```bash
docker compose up -d
```

Create a local environment file:

```bash
cp .env.example .env
```

Start the backend:

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python run.py
```

Start the frontend:

```bash
cd frontend
npm install
npm run dev
```

Run the ML pipeline from the project root:

```bash
python ml/scripts/run_ml_pipeline.py
```

## Notes

- The current version works with imported CSV/ZIP datasets.
- Real-time processing is planned as a future extension.
- Supervised metrics are calculated only when original labels exist.
- Unlabeled datasets are evaluated through anomaly counts and score statistics.