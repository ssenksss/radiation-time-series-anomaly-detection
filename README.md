# Radiation Monitoring Anomaly Detection System

An interactive web-based prototype for radiation level monitoring, anomaly detection, model evaluation, and dataset analysis.
The system combines a Vue dashboard, FastAPI backend, PostgreSQL database, and Python machine learning pipeline for detecting anomalous radiation measurements in time-series data.

This project was developed as part of a Bachelor’s thesis and extended to demonstrate a complete analytical workflow: CSV data ingestion, database storage, ELT processing, feature engineering, machine learning, model evaluation, and dashboard visualization.

---

## 1. Project Overview

The goal of this project is to simulate a radiation monitoring system that can:

* load radiation measurement datasets from CSV files,
* store raw and processed data in a PostgreSQL database,
* transform the data through an ELT pipeline,
* apply machine learning models for anomaly detection,
* calculate model evaluation metrics,
* visualize radiation trends, anomalies, and model performance through a dashboard.

The current version uses a mock radiation dataset. The architecture is prepared so that real measurement data can later replace the mock CSV without changing the main application flow.

---

## 2. Main Features

### Dashboard

The dashboard provides a central overview of the monitoring system, including:

* radiation level time-series chart,
* highlighted anomaly points,
* current radiation level,
* total detected anomalies,
* active alert status,
* model testing summary,
* recent anomaly log,
* dataset shortcut,
* notification alert indicator.

### Dataset Management

The application supports CSV dataset handling. Uploaded or mock datasets are treated as external data sources and stored in PostgreSQL.

Each dataset can be processed through the pipeline and used as the active dataset for dashboard visualization and model evaluation.

### PostgreSQL Database Layer

The system uses PostgreSQL as the central storage layer.

The database stores:

* dataset metadata,
* raw CSV measurements,
* cleaned measurements,
* engineered features,
* anomaly detection results,
* model evaluation metrics,
* application settings such as threshold and active model.

### ELT Pipeline

The data pipeline follows an ELT-style structure:

```text
CSV dataset
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
```

The pipeline includes:

* CSV ingestion,
* timestamp parsing,
* column standardization,
* missing value handling,
* data cleaning,
* feature engineering,
* model training,
* model evaluation,
* database update.

### Machine Learning

The prototype currently implements two anomaly detection models:

* Isolation Forest
* Local Outlier Factor

A third model is included as a planned future improvement:

* Recurrent Neural Network

The active model can be selected from the Settings page. When the detection threshold is changed, the backend starts a fast background pipeline that retrains only the active model and updates the model metrics.

### Model Testing

The Model Testing interface allows comparison between implemented anomaly detection models.

The following metrics are displayed:

* accuracy,
* precision,
* recall,
* false positive rate,
* false negative rate,
* confusion matrix,
* total predicted anomalies.

### Settings

The Settings page allows configuration of:

* detection threshold,
* active anomaly detection model,
* notification options,
* threshold preview chart.

Changing the threshold triggers an optimized background ML pipeline. The dashboard and model metrics are refreshed after the pipeline finishes.

### Notifications

The prototype includes in-app notification logic for anomaly alerts. The alert icon shows only new or unseen alerts, instead of constantly displaying a fixed number of past anomalies.

---

## 3. Technology Stack

### Frontend

* Vue 3
* TypeScript
* Vite
* Chart.js
* Pinia
* Vue Router

### Backend

* Python
* FastAPI
* Uvicorn
* pandas
* NumPy
* scikit-learn
* psycopg2
* python-dotenv

### Database

* PostgreSQL
* Docker Compose support
* SQL schema initialization

### Machine Learning

* Isolation Forest
* Local Outlier Factor
* StandardScaler
* evaluation metrics from scikit-learn

---

## 4. Project Structure

```text
radiation-time-series-anomaly-detection/
├── backend/
│   ├── app/
│   │   ├── database/
│   │   │   ├── connection.py
│   │   │   └── queries.py
│   │   ├── routes/
│   │   │   ├── anomalies.py
│   │   │   ├── datasets.py
│   │   │   ├── measurements.py
│   │   │   ├── model_info.py
│   │   │   ├── pipeline.py
│   │   │   ├── settings.py
│   │   │   └── summary.py
│   │   ├── services/
│   │   │   ├── database_measurement_service.py
│   │   │   ├── database_model_service.py
│   │   │   ├── database_settings_service.py
│   │   │   ├── database_summary_service.py
│   │   │   ├── dataset_upload_service.py
│   │   │   └── pipeline_service.py
│   │   └── main.py
│   ├── requirements.txt
│   └── run.py
│
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── layouts/
│   │   ├── modals/
│   │   ├── services/
│   │   ├── stores/
│   │   ├── types/
│   │   └── views/
│   ├── package.json
│   └── vite.config.ts
│
├── ml/
│   ├── datasets/
│   │   └── mock_radiation_measurements.csv
│   ├── scripts/
│   │   ├── create_features.py
│   │   ├── data_preprocessing.py
│   │   ├── db.py
│   │   ├── evaluate_model.py
│   │   ├── ingest_data.py
│   │   ├── run_ml_pipeline.py
│   │   ├── train_isolation_forest.py
│   │   └── train_lof.py
│   └── outputs/
│
├── database/
│   ├── schema.sql
│   ├── seed_settings.sql
│   └── README.md
│
├── docker-compose.yml
├── .env.example
├── .gitignore
└── README.md
```

---

## 5. Database Design

The PostgreSQL database contains the following main tables:

### `datasets`

Stores metadata about uploaded or mock datasets.

### `raw_measurements`

Stores original measurement records imported from CSV.

### `clean_measurements`

Stores cleaned and standardized measurement data.

### `feature_measurements`

Stores engineered features prepared for machine learning.

### `anomaly_results`

Stores prediction results generated by machine learning models.

### `model_metrics`

Stores evaluation metrics for each model and dataset.

### `app_settings`

Stores application settings such as threshold, active model, and active dataset.

---

## 6. Analytical Workflow

The current mock workflow is:

```text
mock_radiation_measurements.csv
↓
PostgreSQL raw_measurements
↓
clean_measurements
↓
feature_measurements
↓
Isolation Forest / Local Outlier Factor
↓
anomaly_results
↓
model_metrics
↓
FastAPI endpoints
↓
Vue dashboard
```

This satisfies the analytical system requirement by combining:

* external data source simulation,
* database storage,
* ELT transformation,
* machine learning,
* model evaluation,
* dashboard presentation.

---

## 7. Machine Learning Pipeline

The ML pipeline is located in:

```text
ml/scripts/
```

### Full pipeline

The full pipeline is used when importing or processing a dataset:

```bash
python ml/scripts/run_ml_pipeline.py --mode full
```

It performs:

```text
ingestion
↓
preprocessing
↓
feature engineering
↓
Isolation Forest training
↓
LOF training
↓
model evaluation
```

### Fast threshold update pipeline

The fast pipeline is used when the threshold changes from the Settings page:

```bash
python ml/scripts/run_ml_pipeline.py --mode threshold-update
```

It performs:

```text
train only active model
↓
evaluate only active model
↓
update model_metrics
```

This prevents the application from running the full pipeline every time the threshold is changed.

---

## 8. API Endpoints

Main backend endpoints:

```text
GET  /
GET  /measurements
GET  /anomalies
GET  /summary
GET  /model-info
GET  /settings
PUT  /settings/threshold
PUT  /settings/model
GET  /datasets
POST /datasets/upload
GET  /pipeline/status
POST /pipeline/run
```

---

## 9. Environment Configuration

Create a `.env` file in the project root based on `.env.example`.

Example:

```env
DATABASE_URL=postgresql://radiation_user:radiation_password@localhost:5432/radiation_monitoring
```

The `.env` file should not be committed to GitHub.

---

## 10. Running the Project

### 1. Start PostgreSQL

If Docker Compose is configured:

```bash
docker compose up -d
```

### 2. Initialize the database

Run the SQL schema and seed files:

```bash
psql -U radiation_user -d radiation_monitoring -f database/schema.sql
psql -U radiation_user -d radiation_monitoring -f database/seed_settings.sql
```

Depending on local PostgreSQL configuration, connection parameters may need to be adjusted.

### 3. Start the backend

```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Backend runs at:

```text
http://127.0.0.1:8000
```

### 4. Run the ML pipeline for the mock dataset

From the project root:

```bash
python ml/scripts/run_ml_pipeline.py --mode full
```

### 5. Start the frontend

```bash
cd frontend
npm install
npm run dev
```

Frontend runs at:

```text
http://localhost:5173
```

---

## 11. Mock Data Phase

The current version uses a mock radiation measurement dataset:

```text
ml/datasets/mock_radiation_measurements.csv
```

This dataset simulates radiation time-series measurements and contains labels that allow evaluation of anomaly detection performance.

The system is prepared for real CSV data. When real measurements become available, they can be uploaded through the application or processed through the same database and ML pipeline.

---

## 12. Current Status

Implemented:

* Vue dashboard interface
* FastAPI backend
* PostgreSQL database integration
* CSV dataset ingestion
* raw, clean, feature and result data layers
* Isolation Forest model
* Local Outlier Factor model
* model comparison
* model metrics
* confusion matrix
* threshold configuration
* active model configuration
* background ML pipeline
* fast threshold update pipeline
* anomaly log
* dataset management
* notification UI logic

Planned future improvements:

* real radiation dataset integration,
* real-time data streaming,
* IoT sensor connection,
* advanced sequence-based models,
* predictive analytics,
* export reports,
* user authentication.

---

## 13. Academic Context

This project demonstrates how machine learning and interactive visualization can improve radiation monitoring systems.

Compared to traditional threshold-only monitoring, the prototype introduces:

* automated anomaly detection,
* adaptive model-based analysis,
* model comparison,
* structured data storage,
* transparent evaluation metrics,
* interactive dashboard interpretation.

The project also demonstrates a complete data workflow suitable for an analytical prototype:

```text
external data source
↓
database storage
↓
ELT processing
↓
machine learning
↓
evaluation
↓
dashboard visualization
```

---

## 14. Notes

This is a prototype application developed for academic purposes.
The current dataset is synthetic/mock data and should not be used for real radiation safety decisions.

Real deployment would require:

* validated measurement data,
* calibrated sensors,
* real-time ingestion,
* domain expert validation,
* production-grade alerting,
* security and authentication.

---

## 15. Author

Ksenija Raković
Bachelor’s Thesis Project
Radiation Monitoring and Anomaly Detection Prototype
