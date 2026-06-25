# Radiation Monitoring ML Report

Generated at: **2026-06-25 11:59:21**

## 1. Dataset Summary

- Dataset ID: **21**
- Dataset name: **mock_radiation_measurements**
- Original file: **mock_radiation_measurements.csv**
- Source type: **csv**
- Current status: **evaluated**
- Uploaded at: **2026-06-25 07:50:43.680383**
- Time range: **2026-01-01 00:00:00 → 2026-01-07 22:39:00**
- Number of sensors: **1**
- Number of locations: **1**
- Average radiation level: **0.1275 μSv/h**
- Minimum radiation level: **0.0007 μSv/h**
- Maximum radiation level: **0.6928 μSv/h**

## 2. ELT Pipeline Summary

The project follows an ELT pipeline. External CSV or ZIP files are first loaded into the raw layer, then cleaned, transformed, enriched with features and used for machine learning analysis.

| Layer | Table | Row count | Purpose |
|---|---:|---:|---|
| Raw layer | raw_measurements | 10000 | Stores original extracted values from external CSV files. |
| Clean layer | clean_measurements | 10000 | Stores cleaned and standardized radiation measurements. |
| Feature layer | feature_measurements | 10000 | Stores engineered features for ML models. |
| ML results layer | anomaly_results | 20000 | Stores anomaly predictions and anomaly scores. |

## 3. Data Cleaning Summary

- Rows loaded into raw layer: **10000**
- Rows kept after cleaning: **10000**
- Rows removed during cleaning: **0**
- Invalid timestamps and invalid radiation values are removed.
- Temperature and humidity missing values are filled with safe median values.
- Empty sensor IDs are replaced with `UNKNOWN_SENSOR`.
- Empty locations are replaced with `Unknown`.
- Original anomaly labels are normalized when they exist in the dataset.

### Missing Values After Cleaning

| column | missing_values |
| --- | --- |
| radiation_level | 0 |
| temperature | 0 |
| humidity | 0 |
| original_label | 0 |
| anomaly_type | 0 |

## 4. Feature Engineering

The following features are created from cleaned measurements:

| Feature | Description |
|---|---|
| radiation_level | Cleaned radiation measurement value. |
| temperature | Cleaned temperature value. |
| humidity | Cleaned humidity value. |
| hour_of_day | Hour extracted from timestamp. |
| day_of_week | Day of week extracted from timestamp. |
| rolling_mean | Rolling average of radiation level per sensor. |
| rolling_std | Rolling standard deviation of radiation level per sensor. |
| radiation_diff | Difference from the previous radiation value per sensor. |

## 5. Label Availability

- Clean rows: **10000**
- Rows with original labels: **10000**
- Original anomalies: **154**
- Original normal rows: **9846**

If original labels are available, the project can calculate supervised evaluation metrics such as accuracy, precision, recall, FPR and FNR. If real radiation data does not contain labels, the system works in unsupervised anomaly detection mode.

## 6. Model Evaluation

| model_name | accuracy | precision_score | recall_score | fpr | fnr | total_records | total_anomalies |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Isolation Forest | 81.5400 | 0.0770 | 1.0000 | 0.1875 | 0.0000 | 10000 | 2000 |
| Local Outlier Factor | 80.1000 | 0.0410 | 0.5325 | 0.1948 | 0.4675 | 10000 | 2000 |

## 7. Correlation and Dimensionality Reduction Note

A correlation analysis was used to inspect relationships between engineered features. Since the feature set is intentionally small and each feature has a clear time-series interpretation, PCA was not applied in the final prototype.

### Feature Correlation Matrix

| feature | radiation_level | temperature | humidity | hour_of_day | day_of_week | rolling_mean | rolling_std | radiation_diff |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| radiation_level | 1.0000 | 0.3690 | 0.2110 | -0.2890 | -0.0270 | 0.6020 | 0.2530 | 0.5720 |
| temperature | 0.3690 | 1.0000 | 0.4880 | -0.7590 | -0.0010 | 0.6040 | 0.0590 | -0.0000 |
| humidity | 0.2110 | 0.4880 | 1.0000 | -0.4130 | 0.0050 | 0.3340 | 0.0560 | 0.0010 |
| hour_of_day | -0.2890 | -0.7590 | -0.4130 | 1.0000 | 0.0070 | -0.4810 | -0.0320 | 0.0010 |
| day_of_week | -0.0270 | -0.0010 | 0.0050 | 0.0070 | 1.0000 | -0.0420 | 0.0370 | -0.0000 |
| rolling_mean | 0.6020 | 0.6040 | 0.3340 | -0.4810 | -0.0420 | 1.0000 | 0.4380 | -0.0080 |
| rolling_std | 0.2530 | 0.0590 | 0.0560 | -0.0320 | 0.0370 | 0.4380 | 1.0000 | -0.0010 |
| radiation_diff | 0.5720 | -0.0000 | 0.0010 | 0.0010 | -0.0000 | -0.0080 | -0.0010 | 1.0000 |

## 8. Conclusion

The project demonstrates a complete analytical pipeline for radiation monitoring: external data ingestion, raw data storage, cleaning, feature engineering, machine learning anomaly detection, model evaluation and dashboard visualization.

This structure satisfies the requirements for an analytical / ELT-based project and supports the data science part through anomaly detection models and evaluation metrics.
