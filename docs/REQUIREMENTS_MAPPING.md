# Requirements Mapping

This document maps the professor's project requirements to the implemented parts of the Radiation Monitoring Anomaly Detection System.

## Project Scope

The project represents an analytical radiation monitoring system with ELT processing, PostgreSQL analytical storage, machine learning anomaly detection and dashboard visualization.

It is primarily intended to cover:

* the second colloquium requirements related to analytical systems, data lake / data warehouse concepts and ELT processing,
* the final data science project requirements related to data preparation, machine learning and result analysis.

## Requirements Mapping Table

| Professor's Requirement             | Implementation in This Project                                                           | Status    |
| ----------------------------------- | ---------------------------------------------------------------------------------------- | --------- |
| External data source                | Radiation measurements are imported from external CSV or ZIP files.                      | Completed |
| Data extraction                     | CSV / ZIP files are parsed and prepared for ingestion.                                   | Completed |
| Loading into data lake / database   | Raw imported records are stored in PostgreSQL table `raw_measurements`.                  | Completed |
| Data lake-like layered architecture | The project separates raw, clean, feature, ML result and metric layers.                  | Completed |
| ELT process                         | Data is first loaded into PostgreSQL, then transformed through Python scripts.           | Completed |
| Data cleaning                       | Invalid timestamps and invalid radiation values are removed; missing values are handled. | Completed |
| Data standardization                | Different CSV formats and column names are mapped into one unified schema.               | Completed |
| Feature engineering                 | Time-series features are created in `feature_measurements`.                              | Completed |
| Analytical / DWH layer              | SQL views are created for daily, hourly, location-based and model-based analysis.        | Completed |
| Dashboard visualization             | Vue dashboard visualizes radiation levels, anomalies, alerts and model metrics.          | Completed |
| Machine learning model              | Isolation Forest and Local Outlier Factor are implemented for anomaly detection.         | Completed |
| Baseline model                      | Threshold Detection is used as a baseline comparison model.                              | Completed |
| Model comparison                    | Dashboard compares model metrics such as accuracy, precision, recall, FPR and FNR.       | Completed |
| Train/test split                    | `train_test_evaluation.py` creates chronological 70/30 train/test split.                 | Completed |
| Time-series evaluation              | The split is chronological to prevent future data from leaking into training data.       | Completed |
| Model evaluation                    | Metrics are calculated and stored in `model_metrics`.                                    | Completed |
| Report generation                   | `generate_report.py` creates `ml/outputs/ml_report.md`.                                  | Completed |
| Train/test report                   | `train_test_evaluation.py` creates `ml/outputs/train_test_report.md`.                    | Completed |
| Result interpretation               | Reports describe dataset summary, cleaning, features, metrics and conclusion.            | Completed |
| Support for real data               | The system supports future real radiation CSV files through upload and column mapping.   | Completed |

## Implemented Data Flow

```text
External CSV / ZIP source
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
analytics views
        ↓
dashboard visualization
```

## Database Tables

| Table                  | Role                                          |
| ---------------------- | --------------------------------------------- |
| `datasets`             | Stores imported dataset metadata.             |
| `raw_measurements`     | Stores raw extracted records.                 |
| `clean_measurements`   | Stores cleaned and standardized records.      |
| `feature_measurements` | Stores engineered ML features.                |
| `anomaly_results`      | Stores anomaly predictions and scores.        |
| `model_metrics`        | Stores model evaluation metrics.              |
| `app_settings`         | Stores active dataset and threshold settings. |

## Analytical Views

| View                          | Purpose                                   |
| ----------------------------- | ----------------------------------------- |
| `vw_daily_radiation_summary`  | Daily radiation and anomaly aggregation.  |
| `vw_hourly_radiation_summary` | Hourly radiation and anomaly aggregation. |
| `vw_location_anomaly_summary` | Aggregation by location and sensor.       |
| `vw_model_performance`        | Latest model performance metrics.         |
| `vw_latest_anomalies`         | Latest detected anomalies.                |

## Data Science Requirements

The project includes the following data science steps:

1. Data import from external CSV / ZIP files.
2. Raw data storage.
3. Data cleaning.
4. Missing value handling.
5. Feature engineering.
6. Normalization with `StandardScaler`.
7. Machine learning anomaly detection.
8. Chronological train/test split.
9. Model evaluation.
10. Report generation.
11. Dashboard visualization.

## Dimensionality Reduction Note

Dimensionality reduction was considered through correlation analysis.

Since the feature set is small and every feature has a clear time-series meaning, PCA was not applied in the final prototype. This decision keeps the model interpretable and suitable for a radiation monitoring dashboard.

## Real Data Note

The current version uses mock radiation measurements. The system is prepared for real radiation data because it supports CSV / ZIP upload, schema mapping, raw storage, cleaning and feature generation.

If real unlabeled radiation data is imported, the system can still detect anomalies in unsupervised mode. If labels are available, supervised evaluation metrics can also be calculated.

## Conclusion

The project satisfies the analytical and data science requirements through a complete pipeline:

```text
External data source
+ PostgreSQL analytical storage
+ ELT processing
+ data cleaning
+ feature engineering
+ ML anomaly detection
+ train/test evaluation
+ analytical views
+ dashboard visualization
```

This makes the project suitable as a prototype analytical system for radiation monitoring and anomaly detection.
