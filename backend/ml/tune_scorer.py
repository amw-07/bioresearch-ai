"""
Script to tune RandomForest/XGBoost hyperparameters using Optuna.
Saves the best model as scorer_v2.joblib.

Usage:
    uv run python ml/tune_scorer.py
"""

import joblib
import numpy as np
import optuna
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import cross_val_score
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline

# Load synthetic training data (replace paths with your actual data)
try:
    X_train = np.load("backend/ml/data/X_train.npy")
    y_train = np.load("backend/ml/data/y_train.npy")
except FileNotFoundError:
    raise FileNotFoundError("Training data not found. Run `uv run python scripts/generate_training_data.py` first.")

# Define objective function for Optuna
def objective(trial):
    params = {
        "n_estimators": trial.suggest_int("n_estimators", 50, 200),
        "max_depth": trial.suggest_int("max_depth", 3, 15),
        "min_samples_split": trial.suggest_int("min_samples_split", 2, 10),
        "min_samples_leaf": trial.suggest_int("min_samples_leaf", 1, 5),
        "max_features": trial.suggest_categorical("max_features", ["sqrt", "log2", None]),
        "class_weight": trial.suggest_categorical("class_weight", [None, "balanced"]),
    }
    
    model = RandomForestClassifier(**params)
    pipeline = Pipeline([
        ("scaler", StandardScaler()),
        ("clf", model),
    ])
    scores = cross_val_score(pipeline, X_train, y_train, cv=5, scoring="f1_macro")
    return scores.mean()

# Run optimization
print("Starting hyperparameter tuning...")
study = optuna.create_study(direction="maximize")
study.optimize(objective, n_trials=50, timeout=3600)  # 1 hour timeout

# Save best model
print(f"Best params: {study.best_params}")
print(f"Best F1 score: {study.best_value:.4f}")

best_params = study.best_params
best_model = RandomForestClassifier(**best_params)
pipeline = Pipeline([
    ("scaler", StandardScaler()),
    ("clf", best_model),
])
pipeline.fit(X_train, y_train)

# Save the tuned model
joblib.dump({
    "pipeline": pipeline,
    "label_encoder": joblib.load("backend/ml/data/label_encoder.joblib"),
    "model_type": "RandomForest (tuned)",
}, "backend/ml/models/scorer_v2.joblib")

print("✅ Tuned model saved to backend/ml/models/scorer_v2.joblib")