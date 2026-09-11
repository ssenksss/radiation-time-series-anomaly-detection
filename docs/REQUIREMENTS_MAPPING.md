# Requirements Mapping

This document shows how the main bachelor-thesis requirements are covered by the project.

## Thesis title

**Radiation Level Monitoring System with Traditionally Trained Machine Learning Models and a Decision Support Framework Developed Using Generative Artificial Intelligence**

## Project scope

The project is a web prototype for radiation monitoring and anomaly detection. It includes CSV/ZIP import, PostgreSQL storage, ELT processing, feature engineering, traditional machine-learning models, evaluation, analytical views, dashboard visualization and decision support around model outputs.

The current version processes uploaded files. Real-time sensor processing remains a possible future extension.

## Scope separation

| Part | Implementation |
| --- | --- |
| ML training | Conventional Python training scripts |
| ML models | Supervised and unsupervised traditional algorithms |
| ML evaluation | Metrics calculated from stored test predictions and known labels where available |
| Dashboard | Vue and FastAPI application |
| Decision support | Model comparison, status classification, threshold events, alerts and result interpretation |
| GenAI role | Assistance in developing the explanation and decision-support framework, not model training |

## Requirement mapping

| Requirement | How it is covered | Status |
| --- | --- | --- |
| External data source | Measurements are imported from CSV or ZIP files | Done |
| Data extraction | Uploaded files are parsed and standardized before loading | Done |
| Database loading | Original mapped values are stored in `raw_measurements` | Done |
| Raw data layer | `raw_measurements` preserves imported values | Done |
| Clean data layer | `clean_measurements` stores cleaned records | Done |
| Feature layer | `feature_measurements` stores model features | Done |
| Result layer | `anomaly_results` stores predictions and anomaly scores | Done |
| Metric layer | `model_metrics` stores model metrics | Done |
| ELT processing | Data is loaded first and transformed in later database-backed stages | Done |
| Data cleaning | Invalid timestamps and radiation values are removed | Done |
| Schema standardization | Different CSV formats are mapped to a common structure | Done |
| Feature engineering | Time, rolling and difference features are created | Done |
| Analytical views | PostgreSQL views provide reusable summaries | Done |
| Dashboard | Measurements, anomalies, metrics and alerts are displayed | Done |
| Unsupervised ML | Nine anomaly-detection models are implemented | Done |
| Supervised ML | Five classification models are implemented | Done |
| Traditional model training | Models use standard Python ML libraries and explicit fit/predict workflows | Done |
| Train/test split | A chronological 70/30 split is used | Done |
| Leakage prevention | Missing-value replacement and scaling are fitted only on training data | Done |
| Model evaluation | Classification and score metrics are calculated and stored | Done |
| Model comparison | Models are compared in tables, figures and the application | Done |
| ROC/PR curves | Curves are generated from chronological test predictions | Done |
| Confusion matrices | Separate supervised and unsupervised matrices are generated | Done |
| Unlabeled data | Anomaly counts, rate and score statistics are shown without invented labels | Done |
| Labeled data | Classification metrics are calculated against original labels | Done |
| Decision support | The dashboard and reports organize results for interpretation | Done |

## Implemented data flow

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
analytics views
    ↓
dashboard and reports
```

## Database layers

| Table | Role |
| --- | --- |
| `datasets` | Dataset metadata |
| `raw_measurements` | Original imported records |
| `clean_measurements` | Cleaned records and original labels |
| `feature_measurements` | Features prepared for model input |
| `anomaly_results` | Model predictions, scores and split membership |
| `model_metrics` | Calculated evaluation metrics |
| `app_settings` | Active dataset, model and threshold |

## Analytical views

| View | Purpose |
| --- | --- |
| `vw_daily_radiation_summary` | Daily radiation and anomaly summary |
| `vw_hourly_radiation_summary` | Hourly summary |
| `vw_location_anomaly_summary` | Summary by location and sensor |
| `vw_model_performance` | Latest model-performance values |
| `vw_latest_anomalies` | Recent detected anomalies |

## Machine-learning workflow

1. Load and standardize data.
2. Store original mapped values.
3. Clean invalid records.
4. Create time-series features.
5. Split records chronologically.
6. Fit preprocessing only on the training period.
7. Train models and create predictions.
8. Calculate metrics on the final test period.
9. Store results and display them in the application.

The first 70% of timestamp-ordered records form the training set and the last 30% form the test set. This prevents future measurements from being included in model training.

## Implemented models

| Group | Models |
| --- | --- |
| Unsupervised | Isolation Forest, Local Outlier Factor, One-Class SVM, DBSCAN, K-Means, Gaussian Mixture Model, PCA, HBOS and ECOD |
| Supervised | Logistic Regression, Decision Tree, Random Forest, Gradient Boosting and KNN Classifier |

DBSCAN is treated as a clustering baseline because standard DBSCAN does not expose the same reusable prediction workflow for future records as the other operational detectors.

## Evaluation modes

| Mode | Meaning |
| --- | --- |
| `labeled` | Unsupervised model trained without labels and evaluated after prediction using known test labels |
| `supervised` | Supervised classifier trained with labels and evaluated on the chronological test period |
| `unsupervised` | Unlabeled dataset for which only detection and anomaly-score statistics are available |

For labeled evaluation, the project calculates accuracy, precision, recall, F1-score, ROC-AUC, PR-AUC, FPR, FNR, TP, TN, FP, FN and execution time. For unlabeled data, classification metrics remain empty because no ground truth exists.

## Decision-support framework

The decision-support layer includes:

- threshold and model-based status classification
- Critical, Warning, ML Anomaly and Normal states
- current alerts and anomaly log
- model comparison and metric tables
- confusion matrices and ROC/PR curves
- report-ready result interpretation

The traditional models remain separate from the GenAI-assisted development of the explanatory and decision-support layer.
