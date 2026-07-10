# Radiation Monitoring Anomaly Detection System

Bachelor’s thesis project: Radiation Level Monitoring System with Traditionally Trained Machine Learning Models and a Decision Support Framework Developed Using Generative Artificial Intelligence

This repository contains a prototype web application for monitoring radiation measurements and detecting anomalous values in time-series data. The project was developed as part of my Bachelor’s thesis.

The current version works with CSV and ZIP files. After a dataset is imported, the data is stored in PostgreSQL, cleaned, transformed into features and then used for model training and anomaly detection. The same structure could later be extended to work with measurements that arrive in real time.

The machine learning part of the project is based on traditional machine learning models. The models are trained with standard Python libraries and evaluated with standard classification metrics. Generative AI was not used for model training, prediction or metric calculation. In this project, it is treated only as support for the decision-support and explanation part of the application.

This is an academic prototype and should not be treated as a certified radiation safety system.

## Project idea

The main idea of the application is simple:

1. load radiation measurement data
2. store the original values in the database
3. clean and prepare the data
4. create features for machine learning models
5. train traditional ML models
6. detect anomalous measurements
7. compare model results
8. show the results in the dashboard

The system supports two situations:

- datasets that already contain an `is_anomaly` column
- datasets that do not contain anomaly labels

When `is_anomaly` exists, it is used as the original label for evaluation. When it does not exist, the system still performs anomaly detection, but it does not calculate accuracy, precision or recall because there is no ground-truth label to compare with. In that case, the application shows detected anomalies, anomaly rate and anomaly score statistics.

## Data flow

The project follows an ELT-style flow. Data is first loaded into the database and then transformed inside the system.

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
dashboard and reports
```

This separation makes it easier to keep the original imported data, cleaned data, features, predictions and metrics in separate layers.

## Main features

- CSV and ZIP dataset import
- PostgreSQL database storage
- raw, clean and feature data layers
- anomaly detection results stored in the database
- model metrics stored in the database
- Vue dashboard for visualizing radiation levels
- anomaly log and alert status
- model comparison view
- threshold preview
- support for labeled and unlabeled datasets
- traditional supervised and unsupervised machine learning models
- generated evaluation tables and plots

## Technology stack

Frontend:

- Vue 3
- TypeScript
- Vite
- Chart.js
- Pinia

Backend:

- Python
- FastAPI
- Uvicorn
- PostgreSQL

Machine learning and data processing:

- pandas
- NumPy
- scikit-learn
- PyOD models where needed
- StandardScaler

Database and infrastructure:

- PostgreSQL
- Docker Compose
- SQL views

## Database tables

The main database tables are:

| Table | Purpose |
| --- | --- |
| `datasets` | information about imported datasets |
| `raw_measurements` | original imported values |
| `clean_measurements` | cleaned and standardized measurements |
| `feature_measurements` | features used for model training |
| `anomaly_results` | predictions, anomaly scores and status values |
| `model_metrics` | calculated model metrics |
| `app_settings` | active dataset, model and threshold settings |

Analytical SQL views are stored in:

```text
database/analytics_views.sql
```

## Machine learning workflow

The ML workflow is organized in the following steps:

1. data import
2. data cleaning
3. feature creation
4. chronological train/test split
5. model training
6. prediction
7. metric calculation
8. storing predictions and metrics
9. displaying results in the application

Because the data represents a time series, the train/test split is chronological instead of random.

```text
first 70% of records  -> training data
last 30% of records   -> test data
```

This is used to avoid training the model on later measurements and then testing it on earlier ones.

## Unsupervised models

Unsupervised models are important because real radiation data will often arrive without manually prepared labels.

Implemented unsupervised models:

| Model | Reason for use |
| --- | --- |
| Isolation Forest | standard anomaly detection model based on isolating unusual points |
| Local Outlier Factor | detects points with lower local density |
| One-Class SVM | learns the boundary of normal behavior |
| DBSCAN | clustering baseline where noise points are treated as anomalies |
| K-Means Distance | detects points far from the nearest cluster center |
| Gaussian Mixture Model | uses low probability density as anomaly indication |
| PCA Reconstruction Error | uses reconstruction error as anomaly score |
| HBOS | histogram-based outlier scoring |
| ECOD | distribution-based outlier detection |

When labels exist, these models are still trained without using the labels. The labels are used only after prediction, so that the result can be evaluated.

## Supervised models

Supervised models are used only when the dataset contains an original `is_anomaly` column.

Implemented supervised models:

| Model | Reason for use |
| --- | --- |
| Logistic Regression | simple linear baseline |
| Decision Tree | interpretable rule-based model |
| Random Forest | ensemble of decision trees |
| Gradient Boosting | boosting-based classifier |
| KNN Classifier | distance-based classifier |

These models are trained on labeled data and evaluated on the test part of the dataset.

## Evaluation logic

The project separates model type and evaluation mode.

| Mode | Meaning |
| --- | --- |
| `labeled` | unsupervised model trained without labels, but evaluated using available labels |
| `supervised` | supervised model trained and evaluated using labels |
| `unsupervised` | dataset has no labels, so only anomaly statistics are shown |

For labeled and supervised evaluation, the following metrics are calculated:

- accuracy
- precision
- recall
- F1-score
- ROC-AUC
- PR-AUC
- FPR
- FNR
- TP, TN, FP and FN
- training time
- prediction time
- anomaly score statistics

Accuracy is not used as the only important metric because anomalies are rare compared to normal measurements. For that reason, precision, recall, F1-score and PR-AUC are especially important.

## Generated reports and plots

The ML evaluation generates tables and figures in:

```text
ml/outputs/tables/
ml/outputs/figures/
ml/outputs/reports/
```

The generated outputs include:

- full metric comparison table
- table with best results marked
- confusion matrices
- ROC curves
- Precision-Recall curves
- metric comparison bar charts
- training and prediction time charts
- anomaly score box plot
- anomaly score swarm plot
- supervised learning curves
- Gradient Boosting staged performance curve

These files are used as support for the thesis chapter about model evaluation.

## Decision support framework

The decision support part of the application is built around model outputs and stored metrics. It does not replace the ML models and it does not change calculated results.

It helps organize and present:

- current radiation status
- detected anomalies
- anomaly severity labels
- threshold preview
- model comparison
- metric interpretation
- dashboard summaries
- report-ready results

## Project structure

```text
backend/
  app/
    routes/
    services/
    database/
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
  models/
    supervised/
    unsupervised/
  scripts/
  outputs/
    figures/
    reports/
    tables/

docs/
  ELT_ARCHITECTURE.md
  ML_EVALUATION_GUIDE_SR.md
  REQUIREMENTS_MAPPING.md
```

## Running the project

Start PostgreSQL:

```bash
docker compose up -d
```

Start the backend:

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python run.py
```

Start the frontend:

```bash
cd frontend
npm install
npm run dev
```

Run the ML pipeline from the project root when the database is running.

## Notes

- The project currently works with imported CSV/ZIP datasets.
- Real-time data processing is planned as a possible extension.
- Supervised metrics are calculated only when labels exist.
- For real unlabeled datasets, the system reports anomaly detection results without pretending that ground-truth evaluation is available.
