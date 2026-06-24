schema.sql          → PostgreSQL tabele
seed_settings.sql   → početni threshold/model settings
README.md           → kratko objašnjenje baze




connection.py                    → konekcija sa PostgreSQL bazom
queries.py                       → SQL helper funkcije

datasets.py                      → upload CSV endpoint
pipeline.py                      → endpoint za pokretanje pipeline-a ako zatreba

dataset_upload_service.py        → prima CSV i upisuje dataset u bazu
database_measurement_service.py  → čita measurements iz baze
database_summary_service.py      → računa summary iz baze
database_model_service.py        → čita model metrics iz baze
pipeline_service.py              → pokreće ML pipeline iz backend-a




radiation-time-series-anomaly-detection/
├── frontend/
├── backend/
│   ├── app/
│   │   ├── database/
│   │   │   ├── __init__.py
│   │   │   ├── connection.py
│   │   │   └── queries.py
│   │   ├── routes/
│   │   │   ├── datasets.py
│   │   │   └── pipeline.py
│   │   ├── services/
│   │   │   ├── dataset_upload_service.py
│   │   │   ├── database_measurement_service.py
│   │   │   ├── database_summary_service.py
│   │   │   ├── database_model_service.py
│   │   │   └── pipeline_service.py
│   │   └── main.py
│   ├── requirements.txt
│   └── run.py
├── ml/
│   ├── datasets/
│   │   └── mock_radiation_measurements.csv
│   ├── scripts/
│   │   ├── db.py
│   │   ├── ingest_data.py
│   │   ├── data_preprocessing.py
│   │   ├── train_isolation_forest.py
│   │   ├── evaluate_model.py
│   │   └── run_ml_pipeline.py
│   └── outputs/
│       └── .gitkeep
├── database/
│   ├── schema.sql
│   ├── seed_settings.sql
│   └── README.md
├── .env.example
├── README.md
└── .gitignore



==========================================

# Radiation Monitoring Database

This folder contains the PostgreSQL database schema for the radiation monitoring anomaly detection prototype.

## Database role

The database stores:

- uploaded datasets
- raw CSV measurements
- cleaned measurements
- feature-engineered measurements
- anomaly detection results
- model metrics
- application settings

## Data flow

CSV dataset  
→ raw_measurements  
→ clean_measurements  
→ feature_measurements  
→ anomaly_results + model_metrics  
→ FastAPI backend  
→ Vue dashboard

## Main tables

- `datasets` — metadata about uploaded CSV files
- `raw_measurements` — original CSV values
- `clean_measurements` — standardized and cleaned measurements
- `feature_measurements` — ML-ready feature table
- `anomaly_results` — anomaly predictions
- `model_metrics` — evaluation metrics
- `app_settings` — threshold and active dataset settings