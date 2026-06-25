# Radiation Monitoring Anomaly Detection System

This project is a web prototype for monitoring radiation measurements and detecting unusual values in time-series data.

It was developed as part of my Bachelor’s thesis. The main idea was to create an application that can load radiation measurement data, store it in a database, process it, apply anomaly detection models and present the results through a dashboard.

The application is an academic prototype and is not intended to be used as a real radiation safety system.

## About the Project

The system works with radiation measurement datasets imported from CSV or ZIP files. After the data is uploaded, it is stored in PostgreSQL and processed through several steps: raw data storage, cleaning, feature creation, anomaly detection, model evaluation and visualization.

I used PostgreSQL as the main storage layer because I wanted the project to have a clear data structure. The database keeps the original imported data, cleaned measurements, generated features, anomaly detection results and model metrics in separate tables.

The project also includes an ELT-style workflow. Data is first loaded into the database and then transformed through Python scripts. This made it easier to keep the original data separated from the processed data.

## Main Features

The application includes:

* dashboard for radiation level visualization
* CSV and ZIP dataset upload
* PostgreSQL database integration
* data cleaning and standardization
* feature engineering for time-series data
* threshold-based anomaly detection
* Isolation Forest model
* Local Outlier Factor model
* model comparison and evaluation
* train/test evaluation
* analytical SQL views
* generated reports for reviewing the ML pipeline

The dashboard shows radiation measurements, detected anomalies, alert status, model metrics and recent anomaly events.

## Technology Stack

Frontend:

* Vue 3
* TypeScript
* Vite
* Chart.js
* Pinia

Backend:

* Python
* FastAPI
* PostgreSQL
* Uvicorn

Data processing and machine learning:

* pandas
* NumPy
* scikit-learn
* Isolation Forest
* Local Outlier Factor
* StandardScaler

## Data and Database

The project supports a sample labeled dataset and external CSV/ZIP datasets.

The sample dataset is used for testing because it contains anomaly labels. This allows the system to calculate metrics such as accuracy, precision, recall, false positive rate and false negative rate.

External datasets may not contain labels. In that case, the system does not show supervised accuracy, because that would not be reliable. Instead, it shows detected anomalies, anomaly rate, threshold events and model score.

Main database tables:

| Table                  | Description                                          |
| ---------------------- | ---------------------------------------------------- |
| `datasets`             | Stores dataset information.                          |
| `raw_measurements`     | Stores original imported data.                       |
| `clean_measurements`   | Stores cleaned measurements.                         |
| `feature_measurements` | Stores generated features.                           |
| `anomaly_results`      | Stores anomaly predictions and scores.               |
| `model_metrics`        | Stores model evaluation metrics.                     |
| `app_settings`         | Stores active threshold, model and dataset settings. |

## Machine Learning

The project uses a simple threshold method as a baseline and two machine learning models for anomaly detection:

| Model                | Role                                                  |
| -------------------- | ----------------------------------------------------- |
| Threshold Detection  | Baseline model based on selected radiation threshold. |
| Isolation Forest     | ML model for detecting unusual measurements.          |
| Local Outlier Factor | ML model for detecting local outliers.                |

Before applying the models, the data is cleaned and transformed into features such as time-based values, rolling mean, rolling standard deviation and radiation difference.

For the data science part, I added a chronological train/test split. Since the dataset represents a time series, the first 70% of measurements are used for training and the last 30% for testing.

## Analytical Part

Besides the main tables, the project includes SQL views for analytical summaries. These views are used to prepare daily, hourly, location-based and model-based summaries.

They are defined in:

```text
database/analytics_views.sql
```

The project also includes two generated reports:

```text
ml/outputs/ml_report.md
ml/outputs/train_test_report.md
```

These reports summarize the dataset, cleaning process, feature engineering, model metrics and train/test evaluation.

Additional documentation is available in:

```text
docs/ELT_ARCHITECTURE.md
docs/REQUIREMENTS_MAPPING.md
```

## Project Structure

```text
radiation-time-series-anomaly-detection/

backend/
  app/
    routes/
    services/
    database/
    data/
    main.py

frontend/
  src/
    components/
    views/
    services/
    stores/
    router/

database/
  schema.sql
  seed_settings.sql
  analytics_views.sql

ml/
  scripts/
    ingest_data.py
    data_preprocessing.py
    create_features.py
    run_ml_pipeline.py
    train_isolation_forest.py
    train_lof.py
    evaluate_model.py
    generate_report.py
    train_test_evaluation.py
    apply_analytics_views.py
  outputs/

docs/
  ELT_ARCHITECTURE.md
  REQUIREMENTS_MAPPING.md
```

## Running the Project

Start PostgreSQL:

```bash
docker compose up -d
```

Initialize the database:

```bash
psql -U radiation_user -d radiation_monitoring -f database/schema.sql
psql -U radiation_user -d radiation_monitoring -f database/seed_settings.sql
```

Start the backend:

```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Run the ML pipeline from the project root:

```bash
python ml/scripts/run_ml_pipeline.py --mode full
```

Apply analytical views and generate reports:

```bash
python ml/scripts/apply_analytics_views.py
python ml/scripts/generate_report.py
python ml/scripts/train_test_evaluation.py
```

Start the frontend:

```bash
cd frontend
npm install
npm run dev
```

The frontend runs at:

```text
http://localhost:5173
```

The backend runs at:

```text
http://127.0.0.1:8000
```

## Current Status

The current version includes the main parts of the prototype: frontend dashboard, FastAPI backend, PostgreSQL database, CSV/ZIP upload, ELT processing, machine learning anomaly detection, model evaluation, analytical views and generated reports.

Possible future improvements include real-time sensor connection, IoT integration, user authentication, exportable reports and more advanced time-series models.

## Limitations

This project is only an academic prototype. It should not be used for real radiation safety decisions without validated data, calibrated sensors, expert review, production alerting and proper security.

## Author

Ksenija Raković
Bachelor’s Thesis Project
Radiation Monitoring and Anomaly Detection Prototype
