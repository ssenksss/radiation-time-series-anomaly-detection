# ELT Architecture and Analytical Storage Layer

This project implements an analytical data processing pipeline for radiation monitoring and anomaly detection.

The system follows an ELT approach:

1. External data is extracted from CSV or ZIP files.
2. Raw data is loaded into PostgreSQL.
3. Data is cleaned and standardized inside the project pipeline.
4. Time-series features are created for machine learning.
5. ML models detect anomalies.
6. Results and metrics are stored back into PostgreSQL.
7. The dashboard visualizes measurements, anomalies, model metrics and analytical summaries.

## Architecture Overview

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

## External Data Source

The system supports radiation measurement data imported from external CSV or ZIP files.

The upload and ingestion process stores the original extracted data before transformation. This allows the project to preserve the original source values and separate extraction/loading from transformation.

## PostgreSQL as Analytical Storage

PostgreSQL is used as the central analytical storage layer.

Although this is not a cloud-based object storage data lake, the project follows a data lake-like layered architecture:

* raw data is stored first,
* cleaned data is stored separately,
* engineered features are stored in a dedicated layer,
* machine learning results are stored in another layer,
* analytical views are created for reporting and dashboard analysis.

This makes the data flow clear, reproducible and suitable for analytical processing.

## Data Layers

| Layer            | Table                  | Purpose                                                                           |
| ---------------- | ---------------------- | --------------------------------------------------------------------------------- |
| Raw layer        | `raw_measurements`     | Stores original imported records from external files.                             |
| Clean layer      | `clean_measurements`   | Stores cleaned and standardized radiation measurements.                           |
| Feature layer    | `feature_measurements` | Stores engineered time-series features used by ML models.                         |
| ML results layer | `anomaly_results`      | Stores anomaly predictions, anomaly scores and status labels.                     |
| Metrics layer    | `model_metrics`        | Stores model evaluation metrics such as accuracy, precision, recall, FPR and FNR. |

## ELT Process

The project uses ELT instead of traditional ETL.

In this approach, data is first loaded into the database in its raw form. Transformations are then performed through Python scripts and stored in separate PostgreSQL tables.

The main ELT steps are:

| Step                 | Script / Component                              | Description                                                                          |
| -------------------- | ----------------------------------------------- | ------------------------------------------------------------------------------------ |
| Extract              | CSV / ZIP upload                                | External radiation data is imported into the project.                                |
| Load                 | `ingest_data.py`                                | Raw records are loaded into `raw_measurements`.                                      |
| Transform - cleaning | `data_preprocessing.py`                         | Invalid values are removed, missing values are handled and columns are standardized. |
| Transform - features | `create_features.py`                            | Time-series features are created for anomaly detection.                              |
| ML processing        | `run_ml_pipeline.py`                            | Anomaly detection models are applied.                                                |
| Evaluation           | `evaluate_model.py`, `train_test_evaluation.py` | Model performance is calculated and saved.                                           |
| Reporting            | `generate_report.py`                            | A markdown ML report is generated.                                                   |

## Analytics / DWH Views

The project also includes analytical SQL views that represent the reporting layer of the system.

The views are defined in:

```text
database/analytics_views.sql
```

Created views:

| View                          | Purpose                                                |
| ----------------------------- | ------------------------------------------------------ |
| `vw_daily_radiation_summary`  | Daily aggregation of radiation levels and anomalies.   |
| `vw_hourly_radiation_summary` | Hourly aggregation of radiation levels and anomalies.  |
| `vw_location_anomaly_summary` | Aggregation by location and sensor.                    |
| `vw_model_performance`        | Latest model performance metrics.                      |
| `vw_latest_anomalies`         | Latest detected anomalies for dashboard and reporting. |

These views provide a DWH-style analytical layer that supports dashboard visualization and easier reporting.

## Machine Learning Integration

After the ELT process, machine learning models are applied to the prepared feature dataset.

The project includes:

* threshold-based baseline detection,
* Isolation Forest,
* Local Outlier Factor,
* model comparison,
* anomaly scores,
* anomaly status classification,
* model metrics stored in PostgreSQL.

The project also includes a chronological train/test evaluation for the data science part of the project. Since the dataset is a time series, the split is chronological instead of random.

## Conclusion

This architecture satisfies the analytical project requirements because it includes:

* external data extraction,
* PostgreSQL analytical storage,
* raw, clean, feature, result and metrics layers,
* ELT processing,
* data cleaning,
* feature engineering,
* machine learning anomaly detection,
* train/test evaluation,
* analytical SQL views,
* dashboard visualization.

The system therefore represents a complete prototype for radiation monitoring, analytical processing and ML-based anomaly detection.
