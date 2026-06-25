# Radiation Monitoring Anomaly Detection System

An interactive web-based prototype for radiation level monitoring, anomaly detection, model evaluation, dataset processing, and alert simulation. The system combines a Vue 3 dashboard, FastAPI backend, PostgreSQL analytical database, and Python machine learning pipeline for detecting anomalous radiation measurements in time-series data.

This project was developed as part of a Bachelor’s thesis and extended to demonstrate a complete analytical workflow: external CSV/ZIP data ingestion, database storage, ELT processing, feature engineering, machine learning, train/test evaluation, analytical reporting, and dashboard visualization.

---

## 1. Project Overview

The goal of this project is to simulate a radiation monitoring system that can:

* load radiation measurement datasets from CSV or ZIP files,
* support both a labeled sample dataset and external real measurement datasets,
* store raw and processed data in a PostgreSQL analytical database,
* transform the data through an ELT-style pipeline,
* create time-series features for machine learning,
* apply machine learning models for anomaly detection,
* calculate model evaluation metrics when labeled data is available,
* perform chronological train/test evaluation for the data science workflow,
* use threshold-based event detection for unlabeled real datasets,
* create analytical / DWH-style views for reporting,
* visualize radiation trends, anomalies, threshold events, alerts, and model performance through a dashboard.

The application is a **research prototype**, not a production radiation safety system.

---

## 2. Academic Requirements Coverage

This project was developed as a prototype analytical system for radiation monitoring and anomaly detection. It covers the main requirements related to:

* analytical systems,
* ELT data processing,
* data lake / data warehouse-style layered architecture,
* data cleaning and feature engineering,
* machine learning anomaly detection,
* chronological train/test model evaluation,
* analytical reporting,
* dashboard visualization.

The system is designed to support both mock radiation datasets and future real radiation CSV data.

### Requirement Summary

The project includes:

* external CSV / ZIP data import,
* PostgreSQL analytical storage,
* raw / clean / feature / result / metrics layers,
* ELT data flow,
* data cleaning,
* feature engineering,
* machine learning anomaly detection,
* chronological train/test evaluation,
* analytical SQL views,
* interactive dashboard visualization.

This makes the project suitable as an analytical and data science prototype for radiation monitoring and anomaly detection.

---

## 3. ELT and Analytical Architecture

The project follows an ELT pipeline:

```text
External CSV / ZIP data source
        ↓
Raw layer: raw_measurements
        ↓
Clean layer: clean_measurements
        ↓
Feature layer: feature_measurements
        ↓
ML results layer: anomaly_results
        ↓
Metrics layer: model_metrics
        ↓
Analytics views
        ↓
Vue dashboard visualization
```

PostgreSQL is used as the central analytical storage layer. The database is organized into separate layers for raw data, cleaned data, engineered features, anomaly detection results and model metrics.

Although the implementation is not a cloud object-storage data lake, it follows a **data lake-like layered approach** suitable for an academic analytical system prototype.

### Implemented Data Layers

| Layer            | Table                  | Purpose                                                   |
| ---------------- | ---------------------- | --------------------------------------------------------- |
| Raw layer        | `raw_measurements`     | Stores original imported data from external files.        |
| Clean layer      | `clean_measurements`   | Stores cleaned and standardized radiation measurements.   |
| Feature layer    | `feature_measurements` | Stores time-series features used by ML models.            |
| ML results layer | `anomaly_results`      | Stores anomaly predictions, scores and status labels.     |
| Metrics layer    | `model_metrics`        | Stores model evaluation metrics.                          |
| Settings layer   | `app_settings`         | Stores active threshold, active model and active dataset. |

---

## 4. Dataset Support

The system supports two dataset scenarios.

### 4.1 Labeled Sample Dataset

The repository includes a labeled sample dataset:

```text
backend/app/data/mock_radiation_measurements.csv
```

This dataset is used for testing supervised evaluation metrics such as:

* accuracy,
* precision,
* recall,
* false positive rate,
* false negative rate,
* confusion matrix.

The sample dataset is useful for demonstrating model evaluation because it contains anomaly labels.

### 4.2 Real CSV / ZIP Datasets

The application also supports external real radiation datasets uploaded through the Dataset page.

Supported formats:

* `.csv`
* `.zip` containing one or more CSV files

Real datasets may not contain manually labeled anomalies. In that case, the system does not display fake supervised accuracy. Instead, it shows:

* threshold events,
* threshold rate,
* detected anomalies,
* anomaly rate,
* total records,
* model score,
* evaluation mode.

This makes the prototype suitable for both academic model evaluation and real-data monitoring scenarios.

---

## 5. Main Features

### Dashboard

The dashboard provides a central overview of the monitoring system, including:

* radiation level time-series chart,
* threshold line,
* highlighted anomaly/event points,
* current radiation level,
* total detected anomalies/events,
* active alert status,
* summary cards,
* model testing summary,
* recent anomaly log,
* dataset shortcut,
* notification alert indicator.

### Dataset Management

The Dataset page supports:

* CSV upload,
* ZIP upload with multiple CSV files,
* active dataset selection,
* dataset metadata,
* dataset preview,
* number of records,
* active/evaluated dataset status.

Uploaded datasets are treated as external data sources and stored in PostgreSQL. Each dataset can be processed through the pipeline and used as the active dataset for dashboard visualization, anomaly detection, and model evaluation.

### Detection Logic

The system supports two complementary detection concepts.

#### 1. Threshold-based event detection

Records where the radiation level is greater than or equal to the selected threshold are treated as threshold events.

```text
radiation level >= threshold → event / anomaly
radiation level < threshold  → normal
```

This logic is especially useful for real datasets without manually labeled anomalies.

#### 2. Machine learning anomaly detection

The system applies unsupervised machine learning models on engineered time-series features in order to detect unusual measurement patterns.

Currently implemented models:

* Isolation Forest
* Local Outlier Factor

Planned future model:

* Recurrent Neural Network

### Model Testing

The Model Testing interface allows comparison between anomaly detection models.

For labeled datasets, it displays supervised metrics:

* accuracy,
* precision,
* recall,
* false positive rate,
* false negative rate,
* confusion matrix,
* total predicted anomalies.

For real unlabeled datasets, it displays unsupervised indicators:

* model score,
* detected anomalies,
* anomaly rate,
* total records,
* evaluation mode.

Pending models do not display fake metrics.

### Settings

The Settings page allows configuration of:

* detection threshold,
* active anomaly detection model,
* threshold preview,
* dataset range,
* threshold event count,
* threshold event rate,
* notification options,
* threshold preview chart.

Changing the threshold triggers a background ML pipeline and refreshes the model metrics after processing.

### Notifications

The prototype includes in-app notification logic for anomaly alerts. The alert icon shows new or unseen alerts instead of constantly displaying a fixed number of past anomalies.

---

## 6. Technology Stack

### Frontend

* Vue 3
* TypeScript
* Vite
* Vue Router
* Pinia
* Chart.js
* Custom CSS

### Backend

* Python
* FastAPI
* Uvicorn
* PostgreSQL
* psycopg2
* python-dotenv

### Data / Machine Learning

* pandas
* NumPy
* scikit-learn
* Isolation Forest
* Local Outlier Factor
* StandardScaler
* evaluation metrics from scikit-learn

### Infrastructure

* Docker Compose for PostgreSQL
* Git / GitHub

---

## 7. Architecture

The system is organized into five main layers:

```text
External CSV / ZIP dataset
        ↓
FastAPI upload endpoint
        ↓
PostgreSQL analytical database
        ↓
Python ELT + ML pipeline
        ↓
Analytics views
        ↓
Vue dashboard
```

### Frontend Layer

The frontend is responsible for:

* UI/UX,
* dashboard visualization,
* chart rendering,
* anomaly/event log,
* dataset management interface,
* settings interface,
* model testing modal,
* communication with FastAPI endpoints.

### Backend Layer

The backend is responsible for:

* API endpoints,
* dataset upload handling,
* pipeline execution,
* reading data from PostgreSQL,
* sending processed results to the frontend,
* settings updates,
* active model and threshold configuration.

### PostgreSQL Analytical Layer

PostgreSQL is used as the central analytical storage layer.

The database stores:

* dataset metadata,
* raw measurements,
* cleaned measurements,
* engineered features,
* anomaly detection results,
* model metrics,
* application settings.

### ML Pipeline Layer

The Python ML pipeline is responsible for:

* CSV/ZIP ingestion,
* column mapping,
* unit normalization,
* raw data loading,
* data cleaning,
* feature engineering,
* Isolation Forest training,
* LOF training,
* model evaluation,
* saving results and metrics back to PostgreSQL,
* generating academic reports.

### Analytics / DWH Layer

The project also includes an analytical reporting layer implemented through PostgreSQL views.

These views provide daily, hourly, location-based, anomaly-based and model-performance aggregations that can support dashboard visualization and analytical reporting.

---

## 8. Project Structure

```text
radiation-time-series-anomaly-detection/
│
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
│   │   ├── data/
│   │   │   └── mock_radiation_measurements.csv
│   │   └── main.py
│   ├── requirements.txt
│   └── run.py
│
├── database/
│   ├── schema.sql
│   ├── seed_settings.sql
│   ├── analytics_views.sql
│   └── README.md
│
├── docs/
│   ├── ELT_ARCHITECTURE.md
│   └── REQUIREMENTS_MAPPING.md
│
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── layouts/
│   │   ├── router/
│   │   ├── services/
│   │   ├── stores/
│   │   ├── types/
│   │   └── views/
│   ├── package.json
│   └── vite.config.ts
│
├── ml/
│   ├── scripts/
│   │   ├── apply_analytics_views.py
│   │   ├── create_features.py
│   │   ├── csv_column_mapper.py
│   │   ├── data_preprocessing.py
│   │   ├── db.py
│   │   ├── evaluate_model.py
│   │   ├── generate_report.py
│   │   ├── ingest_data.py
│   │   ├── run_ml_pipeline.py
│   │   ├── train_isolation_forest.py
│   │   ├── train_lof.py
│   │   └── train_test_evaluation.py
│   ├── datasets/
│   └── outputs/
│       ├── ml_report.md
│       ├── train_test_report.md
│       └── train_test_metrics.csv
│
├── docker-compose.yml
├── .env.example
├── .gitignore
├── LICENSE
└── README.md
```

---

## 9. Database Design

The PostgreSQL database contains the following main tables.

### datasets

Stores metadata about uploaded or sample datasets.

### raw_measurements

Stores original measurement records imported from CSV files.

### clean_measurements

Stores cleaned and standardized measurement data.

### feature_measurements

Stores engineered time-series features prepared for machine learning.

### anomaly_results

Stores prediction results generated by anomaly detection models.

### model_metrics

Stores evaluation metrics for each model and dataset.

### app_settings

Stores application settings such as:

* active threshold,
* active model,
* active dataset.

---

## 10. Analytical / DWH Views

The project includes a reporting layer implemented through PostgreSQL views.

The SQL definitions are located in:

```text
database/analytics_views.sql
```

Available analytical views:

| View                          | Purpose                                   |
| ----------------------------- | ----------------------------------------- |
| `vw_daily_radiation_summary`  | Daily radiation and anomaly aggregation.  |
| `vw_hourly_radiation_summary` | Hourly radiation and anomaly aggregation. |
| `vw_location_anomaly_summary` | Aggregation by location and sensor.       |
| `vw_model_performance`        | Latest model performance metrics.         |
| `vw_latest_anomalies`         | Latest detected anomalies.                |

These views support analytical reporting and dashboard visualization.

Apply the views with:

```bash
python ml/scripts/apply_analytics_views.py
```

---

## 11. Analytical Workflow

The general workflow is:

```text
CSV / ZIP dataset
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
analytics views
↓
FastAPI endpoints
↓
Vue dashboard
```

This satisfies the analytical system requirement by combining:

* external data source ingestion,
* database storage,
* ELT transformation,
* feature engineering,
* machine learning,
* model evaluation,
* analytical reporting,
* dashboard presentation.

---

## 12. Data Processing Pipeline

The ML pipeline is located in:

```text
ml/scripts/
```

### Full pipeline

The full pipeline is used when importing or processing a dataset:

```bash
python ml/scripts/run_ml_pipeline.py --mode full
```

or with an external dataset:

```bash
python ml/scripts/run_ml_pipeline.py --file path/to/dataset.csv
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
↓
database update
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

## 13. Machine Learning and Evaluation

The project includes three anomaly detection approaches:

| Model                | Role                              |
| -------------------- | --------------------------------- |
| Threshold Detection  | Baseline anomaly detection model. |
| Isolation Forest     | ML-based anomaly detection model. |
| Local Outlier Factor | ML-based anomaly detection model. |

The ML pipeline includes:

* feature preparation,
* normalization with `StandardScaler`,
* anomaly prediction,
* anomaly score generation,
* model comparison,
* accuracy,
* precision,
* recall,
* false positive rate,
* false negative rate.

### Chronological Train/Test Split

For the data science requirement, the project includes a chronological train/test split:

```text
70% earliest measurements → training set
30% latest measurements → test set
```

A chronological split is used because the dataset represents a time series. This prevents future measurements from leaking into the training set.

Train/test evaluation is generated with:

```bash
python ml/scripts/train_test_evaluation.py
```

Generated files:

```text
ml/outputs/train_test_report.md
ml/outputs/train_test_metrics.csv
```

---

## 14. Generated Reports

The project generates additional academic reports.

| Report                              | Generated by                          | Purpose                                                                    |
| ----------------------------------- | ------------------------------------- | -------------------------------------------------------------------------- |
| `ml/outputs/ml_report.md`           | `ml/scripts/generate_report.py`       | Dataset summary, cleaning, feature engineering, ML metrics and conclusion. |
| `ml/outputs/train_test_report.md`   | `ml/scripts/train_test_evaluation.py` | Chronological train/test evaluation report.                                |
| `ml/outputs/train_test_metrics.csv` | `ml/scripts/train_test_evaluation.py` | Exported train/test model metrics.                                         |

Run reports with:

```bash
python ml/scripts/generate_report.py
python ml/scripts/train_test_evaluation.py
```

Apply analytical views with:

```bash
python ml/scripts/apply_analytics_views.py
```

---

## 15. CSV Column Mapping

The system includes a CSV column mapper that supports different column names for:

* timestamp,
* radiation value,
* radiation unit,
* sensor ID,
* location,
* temperature,
* humidity,
* anomaly label,
* anomaly type.

The mapper also handles unit normalization. For example, values in `nSv/h` are converted into `µSv/h`.

If a dataset contains both `location` and `sensor_id`, the UI can display both. If the dataset contains only location information, the UI displays only the location.

---

## 16. API Endpoints

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

## 17. Environment Configuration

Create a `.env` file in the project root based on `.env.example`.

Example:

```env
DATABASE_URL=postgresql://radiation_user:radiation_password@localhost:5432/radiation_monitoring
```

The `.env` file should not be committed to GitHub.

---

## 18. Running the Project

### 1. Start PostgreSQL

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

### 3. Create and activate backend environment

```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 4. Start the backend

```bash
uvicorn app.main:app --reload
```

Backend runs at:

```text
http://127.0.0.1:8000
```

### 5. Run the ML pipeline for the sample dataset

From the project root:

```bash
python ml/scripts/run_ml_pipeline.py --mode full
```

### 6. Apply analytical views

From the project root:

```bash
python ml/scripts/apply_analytics_views.py
```

### 7. Generate academic reports

From the project root:

```bash
python ml/scripts/generate_report.py
python ml/scripts/train_test_evaluation.py
```

### 8. Start the frontend

```bash
cd frontend
npm install
npm run dev
```

Frontend runs at:

```text
http://localhost:5173
```

### 9. Upload a real dataset

Use the Dataset page to upload:

* a CSV file,
* or a ZIP file containing multiple CSV files.

The uploaded dataset is processed through the same PostgreSQL and ML pipeline.

---

## 19. Evaluation Logic

### Labeled sample dataset

The sample dataset contains anomaly labels, so the system can calculate supervised metrics:

* accuracy,
* precision,
* recall,
* false positive rate,
* false negative rate,
* confusion matrix.

### Real unlabeled datasets

Real radiation datasets may not contain manually verified anomaly labels.

In that case, the system does not display fake supervised accuracy. Instead, it displays:

* threshold events,
* threshold rate,
* detected anomalies,
* anomaly rate,
* total records,
* model score,
* evaluation mode.

This distinction is important because real monitoring datasets often do not contain ground-truth anomaly labels.

---

## 20. Documentation

Additional documentation is available in the `docs` folder.

| File                           | Purpose                                                          |
| ------------------------------ | ---------------------------------------------------------------- |
| `docs/ELT_ARCHITECTURE.md`     | Explains the ELT pipeline and analytical storage architecture.   |
| `docs/REQUIREMENTS_MAPPING.md` | Maps professor's requirements to implemented project components. |

These files are included to make the academic structure of the project clear and easy to evaluate.

---

## 21. Requirements Mapping Summary

The project satisfies the analytical and data science requirements through the following implementation.

| Requirement              | Implemented Through                                          |
| ------------------------ | ------------------------------------------------------------ |
| External data source     | CSV / ZIP upload and ingestion.                              |
| Data extraction          | CSV parsing and column mapping.                              |
| Data loading             | Raw records stored in `raw_measurements`.                    |
| Data lake-like structure | Separate raw, clean, feature, result and metrics layers.     |
| ELT processing           | Python scripts transform data after loading into PostgreSQL. |
| Data cleaning            | `data_preprocessing.py`.                                     |
| Feature engineering      | `create_features.py`.                                        |
| Machine learning         | Isolation Forest and Local Outlier Factor.                   |
| Baseline detection       | Threshold Detection.                                         |
| Model evaluation         | `evaluate_model.py` and `model_metrics`.                     |
| Train/test split         | `train_test_evaluation.py`.                                  |
| Reporting                | `generate_report.py` and generated markdown reports.         |
| Analytical / DWH layer   | PostgreSQL views in `analytics_views.sql`.                   |
| Visualization            | Vue dashboard and Chart.js.                                  |

---

## 22. Current Status

Implemented:

* Vue dashboard interface,
* FastAPI backend,
* PostgreSQL database integration,
* sample labeled dataset support,
* real CSV/ZIP dataset upload,
* raw, clean, feature and result data layers,
* CSV column mapping,
* unit normalization,
* ELT-style processing,
* data cleaning,
* feature engineering,
* Isolation Forest model,
* Local Outlier Factor model,
* model comparison,
* model metrics,
* confusion matrix for labeled datasets,
* chronological train/test evaluation,
* generated ML report,
* generated train/test report,
* analytical SQL views,
* threshold configuration,
* active model configuration,
* background ML pipeline,
* fast threshold update pipeline,
* anomaly/event log,
* dataset management,
* threshold preview,
* notification UI logic.

Planned future improvements:

* real-time data streaming,
* IoT sensor connection,
* advanced sequence-based models,
* predictive analytics,
* export reports,
* user authentication.

---

## 23. Academic Context

This project demonstrates how machine learning and interactive visualization can improve radiation monitoring systems.

Compared to traditional threshold-only monitoring, the prototype introduces:

* automated anomaly detection,
* threshold-based event detection,
* adaptive model-based analysis,
* model comparison,
* structured database storage,
* transparent evaluation metrics,
* train/test evaluation,
* analytical reporting,
* interactive dashboard interpretation.

The project also demonstrates a complete data workflow suitable for an analytical/data science prototype:

```text
external data source
↓
database storage
↓
ELT processing
↓
feature engineering
↓
machine learning
↓
evaluation
↓
analytical reporting
↓
dashboard visualization
```

This makes the project suitable as an analytical monitoring prototype and as a Bachelor’s thesis project.

---

## 24. Limitations

This is a prototype application developed for academic purposes.

The system should not be used for real radiation safety decisions without:

* validated measurement data,
* calibrated sensors,
* domain expert validation,
* production-grade alerting,
* security and authentication,
* real-time ingestion infrastructure.

Real unlabeled datasets cannot produce true supervised accuracy metrics unless manually verified anomaly labels are available.

---

## 25. Acknowledgements

The author would like to thank the collaborators from the Vinča Institute of Nuclear Sciences for support, guidance and practical context related to radiation monitoring.

The application is prepared to support real radiation measurement data through CSV / ZIP upload, schema mapping, PostgreSQL storage and the ELT/ML pipeline.

---

## 26. Author

Ksenija Raković
Bachelor’s Thesis Project
Radiation Monitoring and Anomaly Detection Prototype
