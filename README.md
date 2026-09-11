# Radiation Monitoring Anomaly Detection System

Bachelor's thesis project: **Radiation Level Monitoring System with Traditionally Trained Machine Learning Models and a Decision Support Framework Developed Using Generative Artificial Intelligence**

This project is a prototype web application for monitoring radiation measurements and detecting anomalous values in time-series data. It connects dataset import, PostgreSQL storage, ELT processing, traditional machine-learning models and dashboard visualization in one system.

The current version processes CSV and ZIP files. Real-time sensor processing is planned as a future extension. This is an academic prototype and must not be treated as a certified radiation-safety system.

## Project scope

The system supports two types of datasets:

- labeled datasets containing an `is_anomaly` column
- unlabeled datasets without prepared anomaly labels

When labels exist, they are used to train supervised classifiers and to evaluate all models on a chronological test split. Unsupervised models never use these labels during training. When labels do not exist, the system still detects unusual measurements but does not calculate classification metrics without ground truth.

The decision-support layer organizes model results, threshold events, status labels, comparisons and explanations. The machine-learning models themselves are trained through conventional Python workflows; generative AI is not used to fit or alter the models.

## Data flow

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

## Main features

- CSV and ZIP dataset import
- PostgreSQL database storage
- raw, clean, feature, prediction and metric layers
- schema mapping for different radiation CSV formats
- nine unsupervised anomaly-detection models
- five supervised classification models
- chronological train/test evaluation
- anomaly scores, classification metrics and confusion matrices
- ROC and Precision-Recall curves
- dashboard charts, alerts, anomaly log and model comparison
- generated evaluation tables, figures and report

## Technology stack

| Layer            | Technologies                      |
| ---------------- | --------------------------------- |
| Frontend         | Vue 3, TypeScript, Vite, Chart.js |
| Backend          | Python, FastAPI, Uvicorn          |
| Database         | PostgreSQL, SQL views             |
| Machine learning | pandas, NumPy, scikit-learn, PyOD |

## Database tables

| Table                  | Purpose                                        |
| ---------------------- | ---------------------------------------------- |
| `datasets`             | Information about imported datasets            |
| `raw_measurements`     | Original uploaded values                       |
| `clean_measurements`   | Cleaned and standardized measurements          |
| `feature_measurements` | Features used by the models                    |
| `anomaly_results`      | Model predictions, scores and evaluation split |
| `model_metrics`        | Evaluation metrics for every model             |
| `app_settings`         | Active dataset, selected model and threshold   |

## Feature engineering

The models use radiation level, temperature, humidity, time features, rolling radiation statistics and the difference from the previous radiation value. Missing feature values are replaced using medians calculated only from the training period.

## Machine-learning models

### Unsupervised models

| Model                  | Role                             |
| ---------------------- | -------------------------------- |
| Isolation Forest       | Isolation-based anomaly detector |
| Local Outlier Factor   | Local-density detector           |
| One-Class SVM          | Boundary-based detector          |
| DBSCAN                 | Clustering baseline              |
| K-Means                | Distance-from-cluster detector   |
| Gaussian Mixture Model | Probability-density detector     |
| PCA                    | Reconstruction-error detector    |
| HBOS                   | Histogram-based detector         |
| ECOD                   | Empirical-distribution detector  |

### Supervised models

| Model               | Role                          |
| ------------------- | ----------------------------- |
| Logistic Regression | Linear baseline classifier    |
| Decision Tree       | Interpretable tree classifier |
| Random Forest       | Bagging ensemble classifier   |
| Gradient Boosting   | Boosting ensemble classifier  |
| KNN Classifier      | Distance-based classifier     |

The main pipeline always trains the unsupervised models. If the active dataset has usable labels, it also trains and evaluates the five supervised models. Otherwise, that step is skipped with an explanation.

## Evaluation methodology

Because the measurements form a time series, records are ordered by timestamp and split chronologically:

- first 70%: training period
- last 30%: final test period

For labeled datasets, the project reports accuracy, precision, recall, F1-score, ROC-AUC, PR-AUC, FPR, FNR, confusion-matrix values and execution time. Accuracy is not used as the only criterion because anomalies are rare.

For unlabeled datasets, the application reports anomaly count, anomaly rate and anomaly-score statistics instead of unsupported classification metrics.

## Project structure

```text
backend/      FastAPI routes, services and sample datasets
frontend/     Vue application
database/     PostgreSQL schema, seed settings and SQL views
ml/           traditional model training, pipeline scripts and outputs
docs/         architecture and evaluation documentation
```

## Running the project

Start PostgreSQL:

```bash
docker compose up -d
```

Create the environment file:

```bash
cp .env.example .env
```

Start the backend:

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python run.py
```

Start the frontend in a separate terminal:

```bash
cd frontend
npm install
npm run dev
```

Run the complete ML pipeline from the project root:

```bash
python ml/scripts/run_ml_pipeline.py
```

To reproduce the final evaluation dataset included in the repository:

```bash
python ml/scripts/run_ml_pipeline.py --file backend/app/data/mock2.0.csv
python -m ml.scripts.generate_report
```

Generated artifacts are stored in `ml/outputs/tables/`, `ml/outputs/figures/` and `ml/outputs/reports/`.

Additional details are available in:

- `docs/ELT_ARCHITECTURE.md`
- `docs/ML_EVALUATION_GUIDE_SR.md`
- `docs/REQUIREMENTS_MAPPING.md`
