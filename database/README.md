# Radiation Monitoring Database

This folder contains PostgreSQL schema and SQL scripts used by the Radiation Monitoring prototype.

## Files

| File | Purpose |
| --- | --- |
| `schema.sql` | Creates the main database tables |
| `seed_settings.sql` | Inserts initial application settings |
| `analytics_views.sql` | Creates analytical SQL views for reporting |

## Database Role

The database stores:

- uploaded dataset metadata
- raw CSV measurements
- cleaned measurements
- feature-engineered measurements
- anomaly detection results
- model metrics
- application settings

It supports both the traditional ML pipeline and the decision support layer by storing predictions, evaluation metrics and analytical summaries.

## Data Flow

```text
CSV / ZIP dataset
→ raw_measurements
→ clean_measurements
→ feature_measurements
→ anomaly_results
→ model_metrics
→ FastAPI backend
→ Vue dashboard
```

## Main Tables

| Table | Description |
| --- | --- |
| `datasets` | Metadata about uploaded datasets |
| `raw_measurements` | Original imported records |
| `clean_measurements` | Cleaned and standardized records |
| `feature_measurements` | Feature table used by ML models |
| `anomaly_results` | Model predictions and anomaly scores |
| `model_metrics` | Evaluation metrics for each model |
| `app_settings` | Active dataset, threshold and model settings |

## Analytical Views

The file `analytics_views.sql` defines reporting views used by the dashboard:

- `vw_daily_radiation_summary`
- `vw_hourly_radiation_summary`
- `vw_location_anomaly_summary`
- `vw_model_performance`
- `vw_latest_anomalies`
