"""
logistic regression classification model

the model learns from labeled training records
and estimates the probability of the anomaly class
"""

from pathlib import Path
import sys
import time
from typing import Dict, Sequence

import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler


PROJECT_ROOT = Path(__file__).resolve().parents[3]
SCRIPTS_DIR = PROJECT_ROOT / "ml" / "scripts"

for import_path in (PROJECT_ROOT, SCRIPTS_DIR):
    if str(import_path) not in sys.path:
        sys.path.append(str(import_path))


MODEL_NAME = "Logistic Regression"
MODEL_ID = "logistic_regression"
REQUIRES_SCALING = True


def build_model():

    return LogisticRegression(
        max_iter=1000,
        class_weight="balanced",
        random_state=42,
    )


def train_supervised_model(
    train_dataframe: pd.DataFrame,
    test_dataframe: pd.DataFrame,
    full_dataframe: pd.DataFrame,
    feature_columns: Sequence[str],
) -> Dict[str, object]:

    x_train = train_dataframe[list(feature_columns)]
    y_train = train_dataframe["original_label"].astype(int).to_numpy()

    x_test = test_dataframe[list(feature_columns)]
    x_full = full_dataframe[list(feature_columns)]

    # fit the scaler only on training data
    scaler = StandardScaler()

    x_train_scaled = scaler.fit_transform(x_train)
    x_test_scaled = scaler.transform(x_test)
    x_full_scaled = scaler.transform(x_full)

    model = build_model()

    training_started_at = time.time()

    # train only on the training part
    model.fit(
        x_train_scaled,
        y_train,
    )

    training_time_seconds = round(
        time.time() - training_started_at,
        6,
    )

    prediction_started_at = time.time()

    # test predictions are used only for evaluation
    test_predictions = model.predict(
        x_test_scaled
    ).astype(int)

    test_scores = model.predict_proba(
        x_test_scaled
    )[:, 1]

    prediction_time_seconds = round(
        time.time() - prediction_started_at,
        6,
    )

    # full predictions are stored for the application
    full_predictions = model.predict(
        x_full_scaled
    ).astype(int)

    full_scores = model.predict_proba(
        x_full_scaled
    )[:, 1]

    return {
        "test_predictions": test_predictions,
        "test_scores": test_scores,
        "full_predictions": full_predictions,
        "full_scores": full_scores,
        "training_time_seconds": training_time_seconds,
        "prediction_time_seconds": prediction_time_seconds,
    }