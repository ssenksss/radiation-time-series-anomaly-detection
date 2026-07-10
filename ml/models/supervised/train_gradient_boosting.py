"""
gradient boosting classification model

this model builds several small trees one after another
each new tree tries to correct mistakes made by the previous trees
"""

from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[3]
SCRIPTS_DIR = PROJECT_ROOT / "ml" / "scripts"

for import_path in (PROJECT_ROOT, SCRIPTS_DIR):
    if str(import_path) not in sys.path:
        sys.path.append(str(import_path))

import time
from typing import Dict, Sequence

import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import GradientBoostingClassifier


MODEL_NAME = "Gradient Boosting"
MODEL_ID = "gradient_boosting"
REQUIRES_SCALING = False


def build_model():
    # keep model parameters simple and reproducible
    return GradientBoostingClassifier(
        n_estimators=80,
        learning_rate=0.04,
        max_depth=2,
        random_state=42,
    )


def train_supervised_model(
        train_dataframe: pd.DataFrame,
        test_dataframe: pd.DataFrame,
        full_dataframe: pd.DataFrame,
        feature_columns: Sequence[str],
) -> Dict[str, object]:
    model = build_model()

    # use the same feature set for train, test and dashboard predictions
    x_train = train_dataframe[list(feature_columns)]
    y_train = train_dataframe["original_label"].astype(int).to_numpy()
    x_test = test_dataframe[list(feature_columns)]
    x_full = full_dataframe[list(feature_columns)]

    # scale only models that need scaled numeric features
    if REQUIRES_SCALING:
        scaler = StandardScaler()
        x_train_model = scaler.fit_transform(x_train)
        x_test_model = scaler.transform(x_test)
        x_full_model = scaler.transform(x_full)
    else:
        x_train_model = x_train
        x_test_model = x_test
        x_full_model = x_full

    training_started_at = time.time()

    # train the classifier using original anomaly labels
    model.fit(x_train_model, y_train)
    training_time_seconds = round(time.time() - training_started_at, 6)

    prediction_started_at = time.time()

    # test predictions are used for metrics and full predictions are used by the app
    test_predictions = model.predict(x_test_model).astype(int)
    full_predictions = model.predict(x_full_model).astype(int)

    # probability or decision score is used as anomaly score
    if hasattr(model, "predict_proba"):
        test_scores = model.predict_proba(x_test_model)[:, 1]
        full_scores = model.predict_proba(x_full_model)[:, 1]
    elif hasattr(model, "decision_function"):
        test_scores = model.decision_function(x_test_model)
        full_scores = model.decision_function(x_full_model)
    else:
        test_scores = test_predictions.astype(float)
        full_scores = full_predictions.astype(float)

    prediction_time_seconds = round(time.time() - prediction_started_at, 6)

    return {
        "test_predictions": test_predictions,
        "test_scores": test_scores,
        "full_predictions": full_predictions,
        "full_scores": full_scores,
        "training_time_seconds": training_time_seconds,
        "prediction_time_seconds": prediction_time_seconds,
    }
