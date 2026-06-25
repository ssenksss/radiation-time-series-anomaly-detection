# Radiation Monitoring Anomaly Detection System

An interactive web-based prototype for radiation level monitoring, anomaly detection, model evaluation, dataset processing, and alert simulation. The system combines a Vue 3 dashboard, FastAPI backend, PostgreSQL analytical database, and Python machine learning pipeline for detecting anomalous radiation measurements in time-series data.

This project was developed as part of a Bachelor’s thesis and extended to demonstrate a complete analytical workflow: external CSV/ZIP data ingestion, database storage, ELT processing, feature engineering, machine learning, model evaluation, and dashboard visualization.

---

## 1. Project Overview

The goal of this project is to simulate a radiation monitoring system that can:

- load radiation measurement datasets from CSV or ZIP files,
- support both a labeled sample dataset and external real measurement datasets,
- store raw and processed data in a PostgreSQL database,
- transform the data through an ELT-style pipeline,
- apply machine learning models for anomaly detection,
- calculate model evaluation metrics when labeled data is available,
- use threshold-based event detection for unlabeled real datasets,
- visualize radiation trends, anomalies, threshold events, alerts, and model performance through a dashboard.

The application is a **research prototype**, not a production radiation safety system.

---

## 2. Dataset Support

The system supports two dataset scenarios.

### 2.1 Labeled Sample Dataset

The repository includes a labeled sample dataset:

```text
backend/app/data/mock_radiation_measurements.csv
```

This dataset is used for testing supervised evaluation metrics such as:

- accuracy,
- precision,
- recall,
- false positive rate,
- false negative rate,
- confusion matrix.

The sample dataset is useful for demonstrating model evaluation because it contains anomaly labels.

### 2.2 Real CSV / ZIP Datasets

The application also supports external real radiation datasets uploaded through the Dataset page.

Supported formats:

- `.csv`
- `.zip` containing one or more CSV files

Real datasets may not contain manually labeled anomalies. In that case, the system does not display fake supervised accuracy. Instead, it shows:

- threshold events,
- threshold rate,
- detected anomalies,
- anomaly rate,
- total records,
- model score,
- evaluation mode.

This makes the prototype suitable for both academic model evaluation and real-data monitoring scenarios.

---

## 3. Main Features

### Dashboard

The dashboard provides a central overview of the monitoring system, including:

- radiation level time-series chart,
- threshold line,
- highlighted anomaly/event points,
- current radiation level,
- total detected anomalies/events,
- active alert status,
- summary cards,
- model testing summary,
- recent anomaly log,
- dataset shortcut,
- notification alert indicator.

### Dataset Management

The Dataset page supports:

- CSV upload,
- ZIP upload with multiple CSV files,
- active dataset selection,
- dataset metadata,
- dataset preview,
- number of records,
- active/evaluated dataset status.

Uploaded datasets are treated as external data sources and stored in PostgreSQL. Each dataset can be processed through the pipeline and used as the active dataset for dashboard visualization, anomaly detection, and model evaluation.

### Detection Logic

The system supports two complementary detection concepts:

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

- Isolation Forest
- Local Outlier Factor

Planned future model:

- Recurrent Neural Network

### Model Testing

The Model Testing interface allows comparison between anomaly detection models.

For labeled datasets, it displays supervised metrics:

- accuracy,
- precision,
- recall,
- false positive rate,
- false negative rate,
- confusion matrix,
- total predicted anomalies.

For real unlabeled datasets, it displays unsupervised indicators:

- model score,
- detected anomalies,
- anomaly rate,
- total records,
- evaluation mode.

Pending models do not display fake metrics.

### Settings

The Settings page allows configuration of:

- detection threshold,
- active anomaly detection model,
- threshold preview,
- dataset range,
- threshold event count,
- threshold event rate,
- notification options,
- threshold preview chart.

Changing the threshold triggers a background ML pipeline and refreshes the model metrics after processing.

### Notifications

The prototype includes in-app notification logic for anomaly alerts. The alert icon shows new or unseen alerts instead of constantly displaying a fixed number of past anomalies.

---

## 4. Technology Stack

### Frontend

- Vue 3
- TypeScript
- Vite
- Vue Router
- Pinia
- Chart.js
- Custom CSS

### Backend

- Python
- FastAPI
- Uvicorn
- PostgreSQL
- psycopg2
- python-dotenv

### Data / Machine Learning

- pandas
- NumPy
- scikit-learn
- Isolation Forest
- Local Outlier Factor
- StandardScaler
- evaluation metrics from scikit-learn

### Infrastructure

- Docker Compose for PostgreSQL
- Git / GitHub

---

## 5. Architecture

The system is organized into four main layers:

```text
External CSV / ZIP dataset
        ↓
FastAPI upload endpoint
        ↓
PostgreSQL analytical database
        ↓
Python ELT + ML pipeline
        ↓
Vue dashboard
```

### Frontend Layer

The frontend is responsible for:

- UI/UX,
- dashboard visualization,
- chart rendering,
- anomaly/event log,
- dataset management interface,
- settings interface,
- model testing modal,
- communication with FastAPI endpoints.

### Backend Layer

The backend is responsible for:

- API endpoints,
- dataset upload handling,
- pipeline execution,
- reading data from PostgreSQL,
- sending processed results to the frontend,
- settings updates,
- active model and threshold configuration.

### PostgreSQL Analytical Layer

PostgreSQL is used as the central analytical storage layer.

The database stores:

- dataset metadata,
- raw measurements,
- cleaned measurements,
- engineered features,
- anomaly detection results,
- model metrics,
- application settings.

### ML Pipeline Layer

The Python ML pipeline is responsible for:

- CSV/ZIP ingestion,
- column mapping,
- unit normalization,
- raw data loading,
- data cleaning,
- feature engineering,
- Isolation Forest training,
- LOF training,
- model evaluation,
- saving results and metrics back to PostgreSQL.

---

## 6. Project Structure

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
│   └── README.md
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
│   │   ├── create_features.py
│   │   ├── csv_column_mapper.py
│   │   ├── data_preprocessing.py
│   │   ├── db.py
│   │   ├── evaluate_model.py
│   │   ├── ingest_data.py
│   │   ├── run_ml_pipeline.py
│   │   ├── train_isolation_forest.py
│   │   └── train_lof.py
│   ├── datasets/
│   └── outputs/
│
├── docker-compose.yml
├── .env.example
├── .gitignore
├── LICENSE
└── README.md
```

---

## 7. Database Design

The PostgreSQL database contains the following main tables:

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

- active threshold,
- active model,
- active dataset.

---

## 8. Analytical Workflow

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
FastAPI endpoints
↓
Vue dashboard
```

This satisfies the analytical system requirement by combining:

- external data source ingestion,
- database storage,
- ELT transformation,
- feature engineering,
- machine learning,
- model evaluation,
- dashboard presentation.

---

## 9. Data Processing Pipeline

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

## 10. CSV Column Mapping

The system includes a CSV column mapper that supports different column names for:

- timestamp,
- radiation value,
- radiation unit,
- sensor ID,
- location,
- temperature,
- humidity,
- anomaly label,
- anomaly type.

The mapper also handles unit normalization. For example, values in `nSv/h` are converted into `µSv/h`.

If a dataset contains both `location` and `sensor_id`, the UI can display both. If the dataset contains only location information, the UI displays only the location.

---

## 11. API Endpoints

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

## 12. Environment Configuration

Create a `.env` file in the project root based on `.env.example`.

Example:

```env
DATABASE_URL=postgresql://radiation_user:radiation_password@localhost:5432/radiation_monitoring
```

The `.env` file should not be committed to GitHub.

---

## 13. Running the Project

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

### 6. Start the frontend

```bash
cd frontend
npm install
npm run dev
```

Frontend runs at:

```text
http://localhost:5173
```

### 7. Upload a real dataset

Use the Dataset page to upload:

- a CSV file,
- or a ZIP file containing multiple CSV files.

The uploaded dataset is processed through the same PostgreSQL and ML pipeline.

---

## 14. Evaluation Logic

### Labeled sample dataset

The sample dataset contains anomaly labels, so the system can calculate supervised metrics:

- accuracy,
- precision,
- recall,
- false positive rate,
- false negative rate,
- confusion matrix.

### Real unlabeled datasets

Real radiation datasets may not contain manually verified anomaly labels.

In that case, the system does not display fake supervised accuracy. Instead, it displays:

- threshold events,
- threshold rate,
- detected anomalies,
- anomaly rate,
- total records,
- model score,
- evaluation mode.

This distinction is important because real monitoring datasets often do not contain ground-truth anomaly labels.

---

## 15. Current Status

Implemented:

- Vue dashboard interface,
- FastAPI backend,
- PostgreSQL database integration,
- sample labeled dataset support,
- real CSV/ZIP dataset upload,
- raw, clean, feature and result data layers,
- CSV column mapping,
- unit normalization,
- ELT-style processing,
- data cleaning,
- feature engineering,
- Isolation Forest model,
- Local Outlier Factor model,
- model comparison,
- model metrics,
- confusion matrix for labeled datasets,
- threshold configuration,
- active model configuration,
- background ML pipeline,
- fast threshold update pipeline,
- anomaly/event log,
- dataset management,
- threshold preview,
- notification UI logic.

Planned future improvements:

- real-time data streaming,
- IoT sensor connection,
- advanced sequence-based models,
- predictive analytics,
- export reports,
- user authentication.

---

## 16. Academic Context

This project demonstrates how machine learning and interactive visualization can improve radiation monitoring systems.

Compared to traditional threshold-only monitoring, the prototype introduces:

- automated anomaly detection,
- threshold-based event detection,
- adaptive model-based analysis,
- model comparison,
- structured database storage,
- transparent evaluation metrics,
- interactive dashboard interpretation.

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
dashboard visualization
```

This makes the project suitable as an analytical monitoring prototype and as a Bachelor’s thesis project.

---

## 17. Limitations

This is a prototype application developed for academic purposes.

The system should not be used for real radiation safety decisions without:

- validated measurement data,
- calibrated sensors,
- domain expert validation,
- production-grade alerting,
- security and authentication,
- real-time ingestion infrastructure.

Real unlabeled datasets cannot produce true supervised accuracy metrics unless manually verified anomaly labels are available.

---

## 18. Acknowledgements

The author would like to thank the collaborators from the Vinča Institute of Nuclear Sciences for providing access to real radiation measurement data and for supporting the practical validation of the prototype.

The real dataset was used only for academic and research purposes within the scope of this Bachelor’s thesis prototype.

---

## 19. Author

Ksenija Raković  
Bachelor’s Thesis Project  
Radiation Monitoring and Anomaly Detection Prototype