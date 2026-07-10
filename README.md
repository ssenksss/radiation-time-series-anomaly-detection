# Radiation Monitoring Anomaly Detection System

**Bachelor’s thesis project: Radiation Level Monitoring System with Traditionally Trained Machine Learning Models and a Decision Support Framework Developed Using Generative Artificial Intelligence**

This project is a prototype web application for monitoring radiation measurements and detecting anomalous values in time-series data. It was developed as part of my Bachelor’s thesis.

The application currently works with CSV and ZIP datasets. Imported data is stored in PostgreSQL, cleaned, transformed into features and then used for anomaly detection and model comparison. The structure of the project also leaves space for a later extension to real-time measurements.

## Project idea

The main idea is to load radiation measurement data and use machine learning models to detect unusual measurements.

The system supports two types of datasets:

- datasets with an `is_anomaly` column
- datasets without anomaly labels

If `is_anomaly` exists, it is used for model evaluation. If labels do not exist, the system still detects possible anomalies, but it does not calculate supervised metrics such as accuracy, precision or recall.

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

The database keeps imported data, cleaned data, features, model predictions and metrics in separate tables.

## Main features

- CSV and ZIP dataset import
- PostgreSQL storage
- ELT data preparation
- anomaly detection with traditional ML models
- support for labeled and unlabeled datasets
- model comparison view
- anomaly log and alert status
- dashboard for radiation level visualization
- generated reports, tables and plots for model evaluation

## Technologies

**Frontend:** Vue 3, TypeScript, Vite, Chart.js, Pinia  
**Backend:** Python, FastAPI, Uvicorn  
**Database:** PostgreSQL  
**ML/Data processing:** pandas, NumPy, scikit-learn, PyOD

## Database tables

| Table | Purpose |
|---|---|
| `datasets` | information about imported datasets |
| `raw_measurements` | original uploaded measurements |
| `clean_measurements` | cleaned and standardized measurements |
| `feature_measurements` | prepared ML features |
| `anomaly_results` | model predictions and anomaly scores |
| `model_metrics` | evaluation metrics for each model |
| `app_settings` | active dataset, selected model and threshold settings |

## Machine learning workflow

The ML workflow includes:

1. importing data
2. cleaning data
3. creating features
4. splitting data chronologically
5. training models
6. saving predictions and metrics
7. showing results in the dashboard

Since radiation measurements are time-series data, the train/test split is chronological:

```text
first 70% of records -> training data
last 30% of records  -> test data
```

## Models

The project uses both unsupervised and supervised models.

### Unsupervised models

These models are useful when real datasets do not contain anomaly labels.

| Model | Short explanation |
|---|---|
| Isolation Forest | isolates unusual records |
| Local Outlier Factor | compares a record with its local neighbourhood |
| One-Class SVM | learns the boundary of normal measurements |
| DBSCAN | marks low-density points as noise |
| K-Means Distance | uses distance from the nearest cluster center |
| Gaussian Mixture Model | uses probability under learned distributions |
| PCA Reconstruction Error | uses reconstruction error |
| HBOS | uses histogram-based outlier scoring |
| ECOD | uses distribution-based outlier scoring |

### Supervised models

These models are used only when the dataset contains `is_anomaly` labels.

| Model | Short explanation |
|---|---|
| Logistic Regression | simple baseline classifier |
| Decision Tree | interpretable classifier |
| Random Forest | ensemble classifier |
| Gradient Boosting | ensemble model trained step by step |
| KNN Classifier | distance-based classifier |

## Evaluation

For labeled datasets, the following metrics are calculated:

- accuracy
- precision
- recall
- F1-score
- ROC-AUC
- PR-AUC
- FPR and FNR
- TP, TN, FP and FN
- training time
- prediction time

Accuracy is shown, but it is not the only metric used for comparison because anomalies are much rarer than normal measurements.

Generated evaluation files are stored in:

```text
ml/outputs/tables/
ml/outputs/figures/
ml/outputs/reports/
```

## Project structure

```text
backend/      FastAPI backend
frontend/     Vue frontend
database/     SQL schema and views
ml/           ML models, scripts and outputs
docs/         additional documentation
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
- Real-time processing is planned as a possible extension.
- Supervised metrics are calculated only when original labels exist.
- For unlabeled datasets, the application reports detected anomalies and anomaly score statistics.