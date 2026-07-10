# Model Evaluation Report

Generated at: **2026-07-10 12:21:27**

This report is produced by the project script after the model-evaluation step. It summarizes the dataset, used features, trained models, calculated metrics and generated plots.

## 1. Dataset Summary

- Dataset ID: **40**
- Dataset name: **mock_radiation_measurements**
- Original file: **mock_radiation_measurements.csv**
- Source type: **csv**
- Current status: **evaluated**
- Uploaded at: **2026-07-05 16:09:08.776769**
- Time range: **2026-01-01 00:00:00 → 2026-01-07 22:39:00**
- Number of sensors: **1**
- Number of locations: **1**
- Average radiation level: **0.1275 μSv/h**
- Minimum radiation level: **0.0007 μSv/h**
- Maximum radiation level: **0.6928 μSv/h**

## 2. ELT Pipeline Summary

The data pipeline is organized in several steps. The original CSV values are loaded first, then cleaned, transformed into features and finally used for model training, anomaly detection and evaluation.

| Layer | Table | Row count | Purpose |
|---|---:|---:|---|
| Raw layer | raw_measurements | 10000 | Stores values loaded from the original CSV file |
| Clean layer | clean_measurements | 10000 | Stores cleaned radiation measurements |
| Feature layer | feature_measurements | 10000 | Stores features used by the ML models |
| ML results layer | anomaly_results | 140000 | Stores model predictions and anomaly scores |

## 3. Data Cleaning Summary

- Rows loaded into raw layer: **10000**
- Rows kept after cleaning: **10000**
- Rows removed during cleaning: **0**
- Invalid timestamps and invalid radiation values are removed
- Temperature and humidity missing values are filled with median values
- Empty sensor IDs are replaced with `UNKNOWN_SENSOR`
- Empty locations are replaced with `Unknown`
- Original anomaly labels are normalized when they exist in the dataset

### Missing Values After Cleaning

| column | missing_values |
| --- | --- |
| radiation_level | 0 |
| temperature | 0 |
| humidity | 0 |
| original_label | 0 |
| anomaly_type | 0 |

## 4. Feature Engineering

The models use the following input features:

| Feature | Description |
|---|---|
| radiation_level | Cleaned radiation measurement value |
| temperature | Cleaned temperature value |
| humidity | Cleaned humidity value |
| hour_of_day | Hour extracted from timestamp |
| day_of_week | Day of week extracted from timestamp |
| rolling_mean | Rolling average of radiation level per sensor |
| rolling_std | Rolling standard deviation of radiation level per sensor |
| radiation_diff | Difference from the previous radiation value per sensor |

## 5. Label Availability

- Clean rows: **10000**
- Rows with original labels: **10000**
- Original anomalies: **154**
- Original normal rows: **9846**

When labels are available, the models are evaluated on the chronological test split. When labels are missing, the system still detects anomalies, but it reports anomaly count, anomaly rate and score statistics instead of classification metrics.

## 6. Model Selection Rationale

The selected models cover the two cases that the application needs to support. Some datasets have an `is_anomaly` column, while real measurement files may not have manually checked labels.

For that reason, both unsupervised and supervised models are kept. Unsupervised models are needed for real unlabeled measurements. Supervised models are used as a controlled comparison when labels exist, because their predictions can be checked against known anomaly labels.

| Group | Models | Reason for inclusion |
|---|---|---|
| Unsupervised anomaly detection | Isolation Forest, Local Outlier Factor, One-Class SVM, DBSCAN, K-Means Distance, Gaussian Mixture Model, PCA Reconstruction Error, HBOS, ECOD | Used when anomaly labels are not available |
| Supervised classification | Logistic Regression, Decision Tree, Random Forest, Gradient Boosting, KNN Classifier | Used when labels exist and the model can be evaluated directly |

## 7. Evaluation Methodology

The dataset is split chronologically: the first 70% of records are used for training and the last 30% for testing. This is more suitable for time-series data than a random split, because random splitting would mix earlier and later measurements and could give an unrealistically clean evaluation.

When original labels are available, the model predictions are compared with the `is_anomaly` values. The report includes accuracy, precision, recall, F1-score, ROC-AUC, PR-AUC, FPR, FNR and confusion-matrix values. Accuracy is shown, but it is not enough on its own because the dataset contains many more normal measurements than anomalies.

Regression metrics such as MAE, MSE, RMSE and R² are not used as primary metrics in this experiment, because the goal is not to predict the next exact radiation value. The goal is to mark a measurement as normal or anomalous, or to detect unusual points when labels are missing.

For real datasets without labels, accuracy, precision, recall and F1-score are not calculated, because there is no ground-truth label. In that case, the application reports detected anomalies, anomaly rate and anomaly score statistics.

## 8. Model Evaluation Metrics

The table below contains the stored metrics for all evaluated models. For labeled and supervised evaluation, the values are calculated on the chronological test split.

| model_name | evaluation_mode | accuracy | precision_score | recall_score | f1_score | roc_auc | pr_auc | fpr | fnr | tp | tn | fp | fn | true_anomalies | total_records | total_anomalies | anomaly_rate | score_mean | score_std | score_variance | training_time_seconds | prediction_time_seconds | best_result_for |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| DBSCAN | labeled | 98.1700 | 0.4359 | 0.3400 | 0.3820 | 0.9898 | 0.6307 | 0.0075 | 0.6600 | 17 | 2928 | 22 | 33 | 50 | 3000 | 39 | 1.300 | 2.4077 | 1.6676 | 2.7807 | 0.4428 | 0.0003 | prediction_time_seconds |
| ECOD | labeled | 98.2000 | 0.4667 | 0.5600 | 0.5091 | 0.9889 | 0.5453 | 0.0108 | 0.4400 | 28 | 2918 | 32 | 22 | 50 | 3000 | 60 | 2.000 | 0.2119 | 0.0947 | 0.0090 | 0.0678 | 0.0339 |  |
| Gaussian Mixture Model | labeled | 98.1000 | 0.4286 | 0.4200 | 0.4242 | 0.9852 | 0.3966 | 0.0095 | 0.5800 | 21 | 2922 | 28 | 29 | 50 | 3000 | 49 | 1.633 | 0.0280 | 0.0494 | 0.0024 | 0.0203 | 0.0009 |  |
| HBOS | labeled | 95.5700 | 0.2707 | 0.9800 | 0.4242 | 0.9928 | 0.7850 | 0.0447 | 0.0200 | 49 | 2818 | 132 | 1 | 50 | 3000 | 181 | 6.033 | 0.3545 | 0.1245 | 0.0155 | 1.4948 | 0.0048 |  |
| Isolation Forest | labeled | 98.5700 | 0.5538 | 0.7200 | 0.6261 | 0.9915 | 0.6737 | 0.0098 | 0.2800 | 36 | 2921 | 29 | 14 | 50 | 3000 | 65 | 2.167 | -0.1415 | 0.0415 | 0.0017 | 0.1837 | 0.0978 | score_std, score_variance |
| K-Means Distance | labeled | 98.9300 | 0.6875 | 0.6600 | 0.6735 | 0.9804 | 0.5303 | 0.0051 | 0.3400 | 33 | 2935 | 15 | 17 | 50 | 3000 | 48 | 1.600 | 1.8421 | 1.0528 | 1.1084 | 0.4099 | 0.0018 |  |
| Local Outlier Factor | labeled | 93.0300 | 0.1045 | 0.4200 | 0.1673 | 0.4413 | 0.2197 | 0.0610 | 0.5800 | 21 | 2770 | 180 | 29 | 50 | 3000 | 201 | 6.700 | -0.3728 | 0.2909 | 0.0846 | 0.1523 | 0.4396 |  |
| One-Class SVM | labeled | 93.5300 | 0.2049 | 1.0000 | 0.3401 | 0.9861 | 0.3914 | 0.0658 | 0.0000 | 50 | 2756 | 194 | 0 | 50 | 3000 | 244 | 8.133 | -0.8232 | 0.5820 | 0.3387 | 0.0312 | 0.0755 | recall_score, fnr |
| PCA Reconstruction Error | labeled | 97.9700 | 0.4179 | 0.5600 | 0.4786 | 0.9700 | 0.4054 | 0.0132 | 0.4400 | 28 | 2911 | 39 | 22 | 50 | 3000 | 67 | 2.233 | 0.4097 | 0.6986 | 0.4880 | 0.0124 | 0.0019 |  |
| Decision Tree | supervised | 99.9700 | 1.0000 | 0.9800 | 0.9899 | 0.9900 | 0.9803 | 0.0000 | 0.0200 | 49 | 2950 | 0 | 1 | 50 | 3000 | 49 | 1.633 | 0.0163 | 0.1268 | 0.0161 | 0.0090 | 0.0021 | precision_score, fpr |
| Gradient Boosting | supervised | 100.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 0.0000 | 0.0000 | 50 | 2950 | 0 | 0 | 50 | 3000 | 50 | 1.667 | 0.0167 | 0.1236 | 0.0153 | 0.4846 | 0.0081 | accuracy, precision_score, recall_score, f1_score, roc_auc, pr_auc, fpr, fnr |
| KNN Classifier | supervised | 99.9700 | 1.0000 | 0.9800 | 0.9899 | 1.0000 | 1.0000 | 0.0000 | 0.0200 | 49 | 2950 | 0 | 1 | 50 | 3000 | 49 | 1.633 | 0.0165 | 0.1266 | 0.0160 | 0.0034 | 0.3782 | precision_score, roc_auc, pr_auc, fpr, training_time_seconds |
| Logistic Regression | supervised | 94.9700 | 0.2410 | 0.9400 | 0.3837 | 0.9743 | 0.2372 | 0.0502 | 0.0600 | 47 | 2802 | 148 | 3 | 50 | 3000 | 195 | 6.500 | 0.1863 | 0.2074 | 0.0430 | 0.0204 | 0.0005 |  |
| Random Forest | supervised | 99.9700 | 1.0000 | 0.9800 | 0.9899 | 1.0000 | 1.0000 | 0.0000 | 0.0200 | 49 | 2950 | 0 | 1 | 50 | 3000 | 49 | 1.633 | 0.0185 | 0.1058 | 0.0112 | 0.1700 | 0.1071 | precision_score, roc_auc, pr_auc, fpr |

Full metrics CSV: `../tables/model_metrics_full.csv`

Best-marked metrics CSV: `../tables/model_metrics_best_marked.csv`

## 9. Best Results by Metric

If more than one model has the same best value for a metric, all of them are listed in the `best_model` column.

| metric | best_model | value | criterion |
| --- | --- | --- | --- |
| accuracy | Gradient Boosting | 100.0000 | higher is better |
| precision_score | Decision Tree, Gradient Boosting, KNN Classifier, Random Forest | 1.0000 | higher is better |
| recall_score | One-Class SVM, Gradient Boosting | 1.0000 | higher is better |
| f1_score | Gradient Boosting | 1.0000 | higher is better |
| roc_auc | Gradient Boosting, KNN Classifier, Random Forest | 1.0000 | higher is better |
| pr_auc | Gradient Boosting, KNN Classifier, Random Forest | 1.0000 | higher is better |
| fpr | Decision Tree, Gradient Boosting, KNN Classifier, Random Forest | 0.0000 | lower is better |
| fnr | One-Class SVM, Gradient Boosting | 0.0000 | lower is better |
| score_std | Isolation Forest | 0.0415 | lower is better |
| score_variance | Isolation Forest | 0.0017 | lower is better |
| training_time_seconds | KNN Classifier | 0.0034 | lower is better |
| prediction_time_seconds | DBSCAN | 0.0003 | lower is better |

## 10. Result Interpretation

Accuracy is shown in the table, but I did not use it as the only criterion. The dataset is imbalanced, because normal measurements are much more common than anomalies. For that reason, precision, recall, F1-score, PR-AUC and the confusion matrix are more useful for comparing the models.

Among the unsupervised models, K-Means Distance had the best balanced result on the labeled test split, with F1-score 0.673. In this run it made the best compromise between finding anomalies and avoiding too many false alarms.
Isolation Forest also gave a stable result, with F1-score 0.626. This model is useful for the practical version of the application because it can be trained without manually prepared labels.
HBOS was very sensitive to anomalies, with recall 0.980, but its precision was lower (0.271). This means that it detected many true anomalies, but it also produced more false alarms.
One-Class SVM reached recall 1.000, while precision was 0.205. This can be useful when missing an anomaly is a bigger problem than having extra false alarms, but it is not ideal if false alarms need to be low.

### Note on very high supervised results

Several supervised models achieved very high results on the labeled mock dataset. I do not treat this as proof that the same results would be obtained on real radiation data. The mock dataset has clear anomaly labels and the anomalies are easier to separate than they would usually be in practice.

For that reason, the supervised part is used as a controlled experiment. It shows that the feature set and the evaluation pipeline work correctly when labels are available. For real datasets without verified labels, the application uses unsupervised detection and does not report accuracy, precision or recall.

### DBSCAN baseline note

DBSCAN was kept as a clustering-based baseline, not as the main model for the future real-time version. Standard DBSCAN does not train a reusable classifier with a normal `predict` method for new measurements. It groups the currently loaded points and marks low-density points as noise, so the result depends strongly on the selected dataset and parameters.
In this run, DBSCAN achieved F1-score 0.382 and recall 0.340. It can detect a part of the anomalous region, but it is less flexible for later real-time use than models that can be trained once and then applied to new records.

## 11. Generated Figures

The figures are used to support the metric table. Confusion matrices show correct and incorrect predictions, ROC and PR curves show model behavior across thresholds, and box/swarm plots show the distribution of anomaly scores. Learning curves are included for supervised models, where the training size can be varied in a standard way.

### Classification Metrics Bar

![Classification Metrics Bar](../figures/classification_metrics_bar.png)

### Auc Metrics Bar

![Auc Metrics Bar](../figures/auc_metrics_bar.png)

### Training Time Bar

![Training Time Bar](../figures/training_time_bar.png)

### Prediction Time Bar

![Prediction Time Bar](../figures/prediction_time_bar.png)

### Anomaly Score Boxplot

![Anomaly Score Boxplot](../figures/anomaly_score_boxplot.png)

### Anomaly Score Swarm Plot

![Anomaly Score Swarm Plot](../figures/anomaly_score_swarm_plot.png)

### Supervised Learning Curves

![Supervised Learning Curves](../figures/supervised_learning_curves.png)

### Gradient Boosting Staged Performance

![Gradient Boosting Staged Performance](../figures/gradient_boosting_staged_performance.png)

### Confusion Matrices Supervised

![Confusion Matrices Supervised](../figures/confusion_matrices_supervised.png)

### Confusion Matrices Unsupervised

![Confusion Matrices Unsupervised](../figures/confusion_matrices_unsupervised.png)

### Roc Curves

![Roc Curves](../figures/roc_curves.png)

### Precision Recall Curves

![Precision Recall Curves](../figures/precision_recall_curves.png)

## 12. Feature Correlation Matrix

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

## 13. Conclusion

The evaluation shows that the system can train and compare traditional machine-learning models for radiation anomaly detection. The strongest supervised results were obtained on the labeled mock dataset, where anomaly patterns are clearly defined. These results are useful for checking the pipeline, but they should not be treated as guaranteed performance on real radiation-monitoring data.

For the practical version of the application, the unsupervised workflow is especially important. It allows the system to work with real datasets that do not contain an `is_anomaly` column. In that case, the model creates the `predicted_anomaly` result, and the application reports anomaly counts and score statistics instead of supervised metrics.

The comparison table, best-result markers and generated figures can be used later in the thesis discussion and in the Model Testing view of the application.
