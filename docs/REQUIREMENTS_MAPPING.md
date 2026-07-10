# Requirements Mapping

This document shows how the main thesis requirements are covered in the project.

Thesis title:

**Radiation Level Monitoring System with Traditionally Trained Machine Learning Models and a Decision Support Framework Developed Using Generative Artificial Intelligence**

## Project scope

The project is a web prototype for radiation monitoring and anomaly detection. It includes:

- CSV / ZIP data import
- PostgreSQL storage
- ELT-style data processing
- data cleaning
- feature engineering
- traditional machine learning models
- model evaluation
- dashboard visualization
- decision support around model outputs

The current version works with uploaded files. A real-time version is left as a possible extension.

## Scope separation

| Part | Implementation |
| --- | --- |
| ML training | traditional Python ML scripts |
| ML models | supervised and unsupervised algorithms |
| ML evaluation | metrics calculated from stored predictions and test labels where available |
| Dashboard | Vue and FastAPI application |
| Decision support | interpretation of model outputs, metrics, anomaly status and alerts |
| GenAI role | support for the decision-support/explanation layer, not for model training |

## Requirement mapping table

| Requirement | How it is covered | Status |
| --- | --- | --- |
| External data source | data is imported from CSV or ZIP files | done |
| Data extraction | uploaded files are parsed before loading | done |
| Database loading | original values are stored in `raw_measurements` | done |
| Raw data layer | `raw_measurements` keeps imported records | done |
| Clean data layer | `clean_measurements` keeps cleaned records | done |
| Feature layer | `feature_measurements` keeps ML features | done |
| Result layer | `anomaly_results` keeps predictions and scores | done |
| Metric layer | `model_metrics` keeps model metrics | done |
| ELT processing | data is loaded first, then cleaned and transformed | done |
| Data cleaning | invalid timestamps and invalid radiation values are handled | done |
| Schema standardization | different CSV formats are mapped to a common structure | done |
| Feature engineering | time and rolling features are created | done |
| Analytical views | SQL views are used for summaries | done |
| Dashboard | measurements, anomalies, model metrics and alerts are shown | done |
| Unsupervised ML | 9 anomaly detection models are implemented | done |
| Supervised ML | 5 classification models are implemented | done |
| Traditional model training | models are trained with standard ML workflow | done |
| Train/test split | chronological 70/30 split is used | done |
| Model evaluation | metrics are calculated and stored | done |
| Model comparison | models are compared in tables and in the application | done |
| ROC/PR curves | generated for labeled evaluation | done |
| Confusion matrices | generated for evaluated models | done |
| Support for unlabeled data | system reports anomaly statistics when labels are missing | done |
| Support for labeled data | system calculates classification metrics when labels exist | done |
| Decision support framework | dashboard and reports organize model outputs for interpretation | done |

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

## Main database tables

| Table | Role |
| --- | --- |
| `datasets` | stores dataset information |
| `raw_measurements` | stores original imported records |
| `clean_measurements` | stores cleaned records |
| `feature_measurements` | stores features for ML models |
| `anomaly_results` | stores model predictions and anomaly scores |
| `model_metrics` | stores calculated metrics |
| `app_settings` | stores active dataset, model and threshold |

## Analytical views

| View | Purpose |
| --- | --- |
| `vw_daily_radiation_summary` | daily radiation summary |
| `vw_hourly_radiation_summary` | hourly radiation summary |
| `vw_location_anomaly_summary` | anomaly summary by location and sensor |
| `vw_model_performance` | latest model performance values |
| `vw_latest_anomalies` | latest detected anomalies |

## Machine learning part

The ML part follows a standard workflow:

1. load data
2. clean data
3. create features
4. split data chronologically
5. train models
6. predict anomalies
7. calculate metrics
8. store results
9. show results in the dashboard

Because the data is time-series based, the split is chronological:

```text
first 70%  -> train
last 30%   -> test
```

This avoids using future measurements during training.

## Implemented models

### Unsupervised models

| Model | Note |
| --- | --- |
| Isolation Forest | isolation-based anomaly detection |
| Local Outlier Factor | local density based method |
| One-Class SVM | boundary around normal data |
| DBSCAN | clustering baseline |
| K-Means Distance | distance from nearest cluster center |
| Gaussian Mixture Model | probability density based method |
| PCA Reconstruction Error | reconstruction error based method |
| HBOS | histogram-based scoring |
| ECOD | empirical distribution based scoring |

### Supervised models

| Model | Note |
| --- | --- |
| Logistic Regression | simple linear baseline |
| Decision Tree | interpretable classifier |
| Random Forest | ensemble classifier |
| Gradient Boosting | boosting classifier |
| KNN Classifier | distance-based classifier |

## Evaluation modes

The project uses three modes.

| Mode | Meaning |
| --- | --- |
| `labeled` | unsupervised model trained without labels, evaluated with labels after prediction |
| `supervised` | supervised model trained and evaluated with labels |
| `unsupervised` | unlabeled data, only anomaly statistics are shown |

For labeled and supervised modes, the system calculates:

- accuracy
- precision
- recall
- F1-score
- ROC-AUC
- PR-AUC
- FPR
- FNR
- confusion matrix values
- training time
- prediction time

For unlabeled data, these metrics are not calculated because there is no ground-truth label.

## Decision support framework

The decision support part is based on model outputs. It helps the user understand what the model detected and how models compare.

It includes:

- anomaly status labels
- threshold preview
- model comparison
- metric tables
- confusion matrix interpretation
- ROC and PR curve support
- dashboard summaries
- report-ready results

The GenAI part of the thesis is connected to this explanation and decision-support layer. The actual ML models remain traditional models trained through the implemented ML scripts.

## Conclusion

The project covers the required data and ML flow for an academic prototype:

```text
external data source
+ PostgreSQL storage
+ ELT processing
+ feature engineering
+ traditional ML models
+ model evaluation
+ analytical views
+ dashboard visualization
+ decision support framework
```
