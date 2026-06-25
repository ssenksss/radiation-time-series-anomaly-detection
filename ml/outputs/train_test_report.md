# Train/Test Evaluation Report

Generated at: **2026-06-25 12:06:21**

## 1. Purpose

This report documents the train/test evaluation step required for the data science part of the project. Since the dataset is a time series, the split is chronological instead of random, which prevents future measurements from leaking into the training set.

## 2. Dataset and Split

- Dataset ID: **21**
- Dataset name: **mock_radiation_measurements**
- Threshold used for model sensitivity: **0.11 μSv/h**
- Total records used: **10000**
- Training set: **7000 records** (70%)
- Test set: **3000 records** (30%)
- Training time range: **2026-01-01 00:00:00 → 2026-01-05 20:39:00**
- Test time range: **2026-01-05 20:40:00 → 2026-01-07 22:39:00**

## 3. Label Availability

Original anomaly labels are available, so supervised metrics can be calculated on the test set.

- Original anomalies in training set: **104**
- Original anomalies in test set: **50**

## 4. Models

Two anomaly detection models were trained on the training part of the time series and evaluated on the test part:

- Isolation Forest
- Local Outlier Factor with `novelty=True`, which allows prediction on previously unseen test data

## 5. Test Metrics

| model_name | evaluation_mode | train_records | test_records | contamination | predicted_test_anomalies | n_neighbors | accuracy | precision | recall | fpr | fnr | tp | tn | fp | fn |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Isolation Forest | supervised_train_test | 7000 | 3000 | 0.01486 | 70 | N/A | 98.53 | 0.5429 | 0.76 | 0.0108 | 0.24 | 38 | 2918 | 32 | 12 |
| Local Outlier Factor | supervised_train_test | 7000 | 3000 | 0.01486 | 222 | 35 | 92.33 | 0.0946 | 0.42 | 0.0681 | 0.58 | 21 | 2749 | 201 | 29 |

## 6. Conclusion

This report confirms that the project includes a separate model evaluation step with a chronological train/test split. This complements the main dashboard evaluation and provides academic evidence for the machine learning workflow.
