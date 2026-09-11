# ELT Architecture

This document explains the data flow used in the radiation monitoring project.

The project uses an ELT approach. This means that data is first loaded into the database and then transformed through later processing steps.

```text
Extract  ->  Load  ->  Transform
```

In this project, the data comes from CSV or ZIP files. After upload, the original records are saved in PostgreSQL. Cleaning, feature creation, model prediction and metric calculation are then performed on top of the stored data.

## Why ELT is used

ELT is useful here because I want to keep the original imported data and not lose it during cleaning. If something is wrong in a later step, the raw values can still be checked again.

It also makes the project easier to explain because each stage has its own table:

- raw imported data
- cleaned data
- feature data
- model predictions
- model metrics

## Data layers

### 1. Raw layer

Table:

```text
raw_measurements
```

This table stores the values as they were imported from the uploaded file. The goal of this layer is to preserve the original input.

Typical values stored here are:

- timestamp
- radiation level
- sensor id
- location
- temperature
- humidity
- original anomaly label if it exists

### 2. Clean layer

Table:

```text
clean_measurements
```

This layer stores cleaned and standardized measurements.

Cleaning includes:

- removing invalid timestamps
- removing invalid radiation values
- normalizing sensor and location values
- keeping original labels when they exist

Missing temperature and humidity values remain nullable in this layer. Before model fitting, they are replaced with median values calculated only from the chronological training split. This prevents information from the test period from influencing preprocessing.

The important idea is that cleaning prepares the data, but it does not change the meaning of the original measurements.

### 3. Feature layer

Table:

```text
feature_measurements
```

This layer stores the values used by the machine learning models.

The feature set includes:

- radiation level
- temperature
- humidity
- hour of day
- day of week
- rolling mean
- rolling standard deviation
- radiation difference

The rolling features are added because radiation data is time-series based, so the value of one measurement is not completely independent from previous measurements.

### 4. Model result layer

Table:

```text
anomaly_results
```

This table stores the output of each model.

It includes:

- model name
- predicted anomaly value
- anomaly score
- measurement reference
- train/test split membership used for evaluation

This makes it possible to compare different models on the same dataset.

### 5. Metrics layer

Table:

```text
model_metrics
```

This table stores model evaluation results.

When labels are available, the table stores metrics such as:

- accuracy
- precision
- recall
- F1-score
- ROC-AUC
- PR-AUC
- FPR
- FNR
- TP, TN, FP and FN

When labels are not available, the system stores anomaly statistics instead of supervised metrics.

## Full data flow

```text
Uploaded CSV / ZIP file
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
SQL views
        ↓
Dashboard and reports
```

## Analytical views

The project also contains SQL views for easier reporting.

The views are stored in:

```text
database/analytics_views.sql
```

Main views:

| View | Purpose |
| --- | --- |
| `vw_daily_radiation_summary` | daily summary of radiation values and anomalies |
| `vw_hourly_radiation_summary` | hourly summary |
| `vw_location_anomaly_summary` | anomaly summary by location and sensor |
| `vw_model_performance` | model metric overview |
| `vw_latest_anomalies` | recent detected anomalies |

These views are used by the backend and dashboard so that not every summary has to be calculated manually in the frontend.

## Labeled and unlabeled datasets

The architecture supports both labeled and unlabeled data.

If the dataset contains `is_anomaly`, that value is stored as the original label and can be used later for evaluation.

If the dataset does not contain `is_anomaly`, the system can still run unsupervised anomaly detection. In that case, the model creates `predicted_anomaly`, but accuracy and similar metrics are not shown because there is no known true label.

This distinction is important for real radiation data, because real measurements will often not be manually labeled in advance.

## Relation to the dashboard

The dashboard uses the processed data and stored ML results to show:

- current radiation level
- anomaly status
- recent anomalies
- model metrics
- model comparison
- threshold preview
- charts and summaries

The dashboard does not calculate the ML results itself. It displays results that were created by the backend, database and ML scripts.

## Possible real-time extension

The current version imports files, but the same layers can be used later for real-time data.

In a real-time version, new measurements would be inserted into the raw layer as they arrive. The cleaning, feature creation and prediction steps could then be applied to each new batch or each new record.

The planned flow would be:

```text
new sensor measurement
        ↓
raw_measurements
        ↓
cleaning and feature update
        ↓
model prediction
        ↓
anomaly_results
        ↓
dashboard update
```

This is why the database is separated into layers instead of keeping everything in one table.

## Conclusion

The ELT structure is used to make the project easier to maintain and explain. It keeps original data, cleaned data, features, predictions and metrics in separate places. This is useful for both the current CSV-based version and for a possible future version that works with real-time radiation measurements.
