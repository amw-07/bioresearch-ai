#!/usr/bin/env python3
"""
train_scorer.py — XGBoost researcher relevance classifier.

DESIGN DECISIONS:

1. THREE-MODEL COMPARISON (LR vs RF vs XGBoost):
   Winner selected by MACRO F1 — not accuracy, not weighted F1.
   Macro F1 treats all classes equally and does not mask poor performance
   on minority classes (which accuracy and weighted F1 both do).
   This matters because mislabelling "low" researchers as "high" is
   more damaging than a raw accuracy drop.

2. StandardScaler ALWAYS applied:
   XGBoost is scale-invariant — it doesn't need scaling.
   However, if Logistic Regression wins the comparison, it is highly
   sensitive to feature scale. Since we don't know the winner before
   training, we scale all features regardless. Correct engineering decision.

3. SHAP explainer choice:
   TreeExplainer for tree-based models (XGBoost, Random Forest) —
   exact Shapley values via polynomial-time tree traversal.
   LinearExplainer for Logistic Regression — uses the linear model weights.
   The explainer is instantiated after training and the winner is determined.

4. eval_v1.json structure is LOCKED — the frontend ModelMetricsDashboard.tsx
   reads this exact schema. Do not add, remove, or rename top-level keys.
"""

import json
import sys
import warnings
from datetime import datetime
from pathlib import Path
from typing import Dict, Tuple

import joblib
import numpy as np
import pandas as pd
import shap
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix, f1_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import LabelEncoder, StandardScaler
from xgboost import XGBClassifier

warnings.filterwarnings("ignore")

ROOT = Path(__file__).parent.parent
DATA_PATH = ROOT / "data" / "training_researchers.csv"
MODEL_DIR = ROOT / "ml" / "models"
REPORT_DIR = ROOT / "ml" / "reports"
MODEL_PATH = MODEL_DIR / "scorer_v1.joblib"
EVAL_PATH = REPORT_DIR / "eval_v1.json"

FEATURES = [
    "has_recent_pub",
    "pub_count_norm",
    "h_index_norm",
    "recency_score",
    "has_nih_active",
    "nih_award_norm",
    "institution_funding",
    "seniority_score",
    "is_senior_researcher",
    "title_relevance",
    "domain_coverage_score",
    "abstract_relevance_score",
    "has_contact",
    "contact_confidence",
    "has_linkedin_verified",
    "is_conference_speaker",
    "institution_type_score",
    "location_hub_score",
]

FEATURE_DISPLAY_NAMES: Dict[str, str] = {
    "has_recent_pub": "Recent Publication",
    "pub_count_norm": "Publication Volume",
    "h_index_norm": "Citation Impact (h-index)",
    "recency_score": "Research Recency",
    "has_nih_active": "Active NIH Grant",
    "nih_award_norm": "NIH Funding Level",
    "institution_funding": "Institution Resources",
    "seniority_score": "Seniority Level",
    "is_senior_researcher": "Senior Researcher (PI/Prof)",
    "title_relevance": "Domain Keyword Coverage",
    "domain_coverage_score": "Biotech Domain Breadth",
    "abstract_relevance_score": "Abstract Semantic Relevance",
    "has_contact": "Contact Discoverable",
    "contact_confidence": "Contact Confidence",
    "has_linkedin_verified": "LinkedIn Verified",
    "is_conference_speaker": "Conference Speaker",
    "institution_type_score": "Institution Type",
    "location_hub_score": "Research Hub Location",
}

LABEL_ORDER = ["high", "medium", "low"]


def load_data() -> Tuple[np.ndarray, np.ndarray, LabelEncoder]:
    """Load training CSV and prepare feature matrix + encoded labels."""
    df = pd.read_csv(DATA_PATH)

    missing = [feature for feature in FEATURES if feature not in df.columns]
    if missing:
        raise ValueError(f"Missing feature columns in training data: {missing}")

    X = df[FEATURES].values
    le = LabelEncoder()
    le.fit(LABEL_ORDER)
    y = le.transform(df["label"].values)

    print(f"Loaded {len(X)} samples with {X.shape[1]} features")
    print(f"Label distribution: {{ {', '.join(f'{label!r}: {int((y == i).sum())}' for i, label in enumerate(le.classes_))} }}")
    return X, y, le


def build_candidates() -> Dict[str, Pipeline]:
    """Build three candidate pipelines. Scaler applied to all."""
    return {
        "LogisticRegression": Pipeline(
            [
                ("scaler", StandardScaler()),
                (
                    "clf",
                    LogisticRegression(
                        max_iter=1000,
                        class_weight="balanced",
                        C=1.0,
                        random_state=42,
                    ),
                ),
            ]
        ),
        "RandomForest": Pipeline(
            [
                ("scaler", StandardScaler()),
                (
                    "clf",
                    RandomForestClassifier(
                        n_estimators=100,
                        class_weight="balanced",
                        random_state=42,
                        n_jobs=-1,
                    ),
                ),
            ]
        ),
        "XGBClassifier": Pipeline(
            [
                ("scaler", StandardScaler()),
                (
                    "clf",
                    XGBClassifier(
                        n_estimators=200,
                        max_depth=4,
                        learning_rate=0.05,
                        subsample=0.8,
                        colsample_bytree=0.8,
                        use_label_encoder=False,
                        eval_metric="mlogloss",
                        random_state=42,
                        n_jobs=-1,
                        verbosity=0,
                    ),
                ),
            ]
        ),
    }


def evaluate(pipeline: Pipeline, X_test: np.ndarray, y_test: np.ndarray, le: LabelEncoder) -> Dict:
    """Compute evaluation metrics. Returns dict matching eval_v1.json schema."""
    y_pred = pipeline.predict(X_test)
    accuracy = float(accuracy_score(y_test, y_pred))
    macro_f1 = float(f1_score(y_test, y_pred, average="macro"))

    report = classification_report(y_test, y_pred, target_names=le.classes_, output_dict=True)
    cm = confusion_matrix(y_test, y_pred).tolist()

    per_class = {}
    for label in LABEL_ORDER:
        if label in report:
            per_class[label] = {
                "precision": round(report[label]["precision"], 4),
                "recall": round(report[label]["recall"], 4),
                "f1": round(report[label]["f1-score"], 4),
            }

    return {
        "accuracy": round(accuracy, 4),
        "macro_f1": round(macro_f1, 4),
        "per_class": per_class,
        "confusion_matrix": cm,
    }


def get_feature_importances(pipeline: Pipeline) -> list:
    """Extract top-10 feature importances regardless of model type."""
    clf = pipeline.named_steps["clf"]
    if hasattr(clf, "feature_importances_"):
        importances = clf.feature_importances_
    elif hasattr(clf, "coef_"):
        importances = np.mean(np.abs(clf.coef_), axis=0)
    else:
        return []

    pairs = sorted(zip(FEATURES, importances), key=lambda x: x[1], reverse=True)
    return [
        {"feature": feature, "display_name": FEATURE_DISPLAY_NAMES[feature], "importance": round(float(importance), 6)}
        for feature, importance in pairs[:10]
    ]


def get_shap_explainer(pipeline: Pipeline, X_train: np.ndarray):
    """
    Instantiate SHAP explainer appropriate for the winning model type.
    """
    clf = pipeline.named_steps["clf"]
    scaler = pipeline.named_steps["scaler"]
    X_train_scaled = scaler.transform(X_train)

    if isinstance(clf, (XGBClassifier, RandomForestClassifier)):
        explainer = shap.TreeExplainer(clf)
    else:
        explainer = shap.LinearExplainer(clf, X_train_scaled)

    return explainer


def main():
    X, y, le = load_data()
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    candidates = build_candidates()
    results = {}

    print("\n── Training candidates ──────────────────────────────────────")
    for name, pipeline in candidates.items():
        print(f"  Training {name}...", end=" ")
        pipeline.fit(X_train, y_train)
        metrics = evaluate(pipeline, X_test, y_test, le)
        results[name] = (pipeline, metrics)
        print(f" macro_f1={metrics['macro_f1']:.4f} accuracy={metrics['accuracy']:.4f}")

    winner_name = max(results, key=lambda key: results[key][1]["macro_f1"])
    winner_pipeline, winner_metrics = results[winner_name]

    print(f"\n── Winner: {winner_name} (macro_f1={winner_metrics['macro_f1']:.4f}) ──────")

    if winner_metrics["macro_f1"] < 0.70:
        print(f"\n⚠️  WARNING: macro F1 = {winner_metrics['macro_f1']:.4f} < 0.70")
        print("   Training data may have too little variance in abstract_relevance_score")
        print("   or domain_coverage_score. Inspect data/training_researchers.csv")
        sys.exit(1)

    top_features = get_feature_importances(winner_pipeline)
    top_feature_names = [feature["feature"] for feature in top_features[:5]]
    print(f"\nTop 5 features: {top_feature_names}")

    key_features = {"domain_coverage_score", "abstract_relevance_score"}
    missing_key = key_features - set(top_feature_names)
    if missing_key:
        print(f"⚠️  WARNING: {missing_key} not in top 5 — check training data variance")

    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)

    save_payload = {
        "pipeline": winner_pipeline,
        "label_encoder": le,
        "feature_names": FEATURES,
        "feature_display_names": FEATURE_DISPLAY_NAMES,
        "model_type": winner_name,
    }
    joblib.dump(save_payload, MODEL_PATH)
    print(f"\n✓ Model saved → {MODEL_PATH}")

    eval_report = {
        "model_type": winner_name,
        "trained_at": datetime.utcnow().isoformat() + "Z",
        "n_training_samples": len(X_train),
        "n_test_samples": len(X_test),
        "test_accuracy": winner_metrics["accuracy"],
        "macro_f1": winner_metrics["macro_f1"],
        "per_class": winner_metrics["per_class"],
        "confusion_matrix": winner_metrics["confusion_matrix"],
        "top_10_features": top_features,
    }

    with open(EVAL_PATH, "w", encoding="utf-8") as file:
        json.dump(eval_report, file, indent=2)
    print(f"✓ Eval report saved → {EVAL_PATH}")

    print("\n── All model results ───────────────────────────────────────")
    for name, (_, metrics) in results.items():
        marker = "★" if name == winner_name else " "
        print(f"  {marker} {name}: macro_f1={metrics['macro_f1']:.4f} accuracy={metrics['accuracy']:.4f}")

    print(f"\n── Confusion matrix ({winner_name}) ─────────────────────────")
    cm = winner_metrics["confusion_matrix"]
    labels_display = le.classes_
    print(f"{'':15s} " + "  ".join(f"{label:8s}" for label in labels_display))
    for index, row in enumerate(cm):
        print(f"  actual {labels_display[index]:6s}: " + "  ".join(f"{value:8d}" for value in row))

    print(f"\n🎉  Training complete. macro_f1 = {winner_metrics['macro_f1']:.4f}")


if __name__ == "__main__":
    main()
