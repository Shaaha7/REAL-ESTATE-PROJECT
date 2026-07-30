"""
Standalone, reproducible training + evaluation script for a real lead-conversion
classifier (XGBClassifier + SMOTE + stratified k-fold CV).

Run from backend/:
    python scripts/train_classifier.py

Why two runs are reported
--------------------------
The repo has two candidate datasets, and they support very different claims:

1. PRIMARY  - data/synthetic/leads_200.csv, target = status == "closed"
   (converted) vs everything else (lost / still active in the pipeline).
   This is the only outcome field in the repo that is NOT a deterministic
   function of the engineered scoring features - it was generated
   independently. That makes it the only honest test of whether these
   features actually predict a real-world-shaped outcome.

2. DIAGNOSTIC - data/synthetic/lead_training_data_3000.csv, target =
   lead_score_target >= 75 (the existing HOT-tier cutoff). Included ONLY to
   show why this version of the number is inflated: lead_score_target is a
   hand-built weighted-sum formula over these same features plus Gaussian
   noise (see LeadScoringAgent.train_lead_scorer's synthetic fallback), so a
   classifier here is largely re-deriving arithmetic it was handed the
   inputs to, not predicting anything. Do not quote this run's numbers as a
   real-world capability claim.

Methodology notes
------------------
- SMOTE is fit and applied ONLY on each fold's training split, never on the
  held-out fold - resampling before splitting (or fitting SMOTE across the
  whole dataset) would leak synthetic neighbours of test points into
  training and inflate every metric.
- Features for the 200-lead run are computed with the exact same formula as
  LeadScoringAgent._build_features(), so this evaluates the same feature
  representation the live API actually uses at inference time.
- Numbers below are whatever the data produced. Nothing here was tuned
  toward a target score.
"""
from __future__ import annotations
import json
from pathlib import Path

import numpy as np
import pandas as pd
from imblearn.over_sampling import SMOTE
from sklearn.model_selection import StratifiedKFold
from sklearn.metrics import roc_auc_score, f1_score, precision_score, recall_score
from xgboost import XGBClassifier

RANDOM_STATE = 42
N_SPLITS = 5
BACKEND_DIR = Path(__file__).resolve().parent.parent
FEATURE_COLS = [
    "budget_normalized", "urgency_score", "engagement_score",
    "property_match_score", "response_time_score",
    "communication_quality_score", "location_preference_match",
]


def engineer_features_from_raw(df: pd.DataFrame) -> pd.DataFrame:
    """Mirrors LeadScoringAgent._build_features() exactly, vectorised."""
    return pd.DataFrame({
        "budget_normalized": (df["budget_aed"] / 20_000_000).clip(upper=1.0),
        "urgency_score": (100 - df["timeline_months"].fillna(12) * 8.33).clip(lower=0.0),
        "engagement_score": (df["num_interactions"] * 10).clip(upper=100.0),
        "property_match_score": np.where(df["bedrooms"].notna() & (df["bedrooms"] > 0), 80.0, 50.0),
        "response_time_score": (100 - (df["avg_response_hours"] / 24) * 10).clip(lower=0.0),
        "communication_quality_score": df["message_quality_score"] * 100,
        "location_preference_match": np.where(df["location_preference"].fillna("").astype(str).str.len() > 0, 1.0, 0.5),
    })


def run_cv(X: pd.DataFrame, y: np.ndarray, label: str) -> dict:
    skf = StratifiedKFold(n_splits=N_SPLITS, shuffle=True, random_state=RANDOM_STATE)
    fold_metrics = []
    for fold_i, (train_idx, test_idx) in enumerate(skf.split(X, y), start=1):
        X_train, X_test = X.iloc[train_idx], X.iloc[test_idx]
        y_train, y_test = y[train_idx], y[test_idx]

        sm = SMOTE(random_state=RANDOM_STATE)
        X_train_res, y_train_res = sm.fit_resample(X_train, y_train)

        clf = XGBClassifier(
            n_estimators=200, max_depth=5, learning_rate=0.05,
            random_state=RANDOM_STATE, eval_metric="logloss", verbosity=0,
        )
        clf.fit(X_train_res, y_train_res)

        proba = clf.predict_proba(X_test)[:, 1]
        pred = clf.predict(X_test)

        m = {
            "fold": fold_i,
            "test_size": int(len(y_test)),
            "test_positives": int(y_test.sum()),
            "auc_roc": float(roc_auc_score(y_test, proba)),
            "f1": float(f1_score(y_test, pred, zero_division=0)),
            "precision": float(precision_score(y_test, pred, zero_division=0)),
            "recall": float(recall_score(y_test, pred, zero_division=0)),
        }
        fold_metrics.append(m)
        print(f"  [{label}] fold {fold_i}: AUC={m['auc_roc']:.4f} F1={m['f1']:.4f} "
              f"P={m['precision']:.4f} R={m['recall']:.4f}  (n_test={m['test_size']}, pos={m['test_positives']})")

    agg = {
        metric: {
            "mean": float(np.mean([f[metric] for f in fold_metrics])),
            "std": float(np.std([f[metric] for f in fold_metrics])),
        }
        for metric in ("auc_roc", "f1", "precision", "recall")
    }
    return {"label": label, "n_samples": int(len(y)), "n_positive": int(y.sum()),
            "positive_rate": float(y.mean()), "folds": fold_metrics, "aggregate": agg}


def primary_run() -> dict:
    df = pd.read_csv(BACKEND_DIR / "data/synthetic/leads_200.csv")
    X = engineer_features_from_raw(df)
    y = (df["status"] == "closed").astype(int).to_numpy()
    print(f"\n=== PRIMARY: leads_200.csv, target = status=='closed' ===")
    print(f"n={len(y)}, positives={y.sum()} ({y.mean():.1%}), status breakdown:")
    print(df["status"].value_counts().to_string())
    return run_cv(X, y, "primary_leads200_status_closed")


def diagnostic_run() -> dict:
    df = pd.read_csv(BACKEND_DIR / "data/synthetic/lead_training_data_3000.csv")
    X = df[FEATURE_COLS]
    y = (df["lead_score_target"] >= 75).astype(int).to_numpy()
    print(f"\n=== DIAGNOSTIC (leakage demo): lead_training_data_3000.csv, target = lead_score_target>=75 ===")
    print(f"n={len(y)}, positives={y.sum()} ({y.mean():.1%})")
    return run_cv(X, y, "diagnostic_3000_score_threshold")


def main():
    primary = primary_run()
    diagnostic = diagnostic_run()

    results = {
        "methodology": "StratifiedKFold(n_splits=5), SMOTE fit on train fold only, XGBClassifier",
        "primary": primary,
        "diagnostic_leakage_demo": diagnostic,
    }
    out_path = BACKEND_DIR / "data/evaluation/classifier_results.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(results, indent=2))

    print("\n" + "=" * 70)
    print("FINAL (5-fold mean +/- std)")
    print("=" * 70)
    for run in (primary, diagnostic):
        a = run["aggregate"]
        print(f"\n{run['label']}  (n={run['n_samples']}, positive rate={run['positive_rate']:.1%})")
        print(f"  AUC-ROC:   {a['auc_roc']['mean']:.4f} +/- {a['auc_roc']['std']:.4f}")
        print(f"  F1:        {a['f1']['mean']:.4f} +/- {a['f1']['std']:.4f}")
        print(f"  Precision: {a['precision']['mean']:.4f} +/- {a['precision']['std']:.4f}")
        print(f"  Recall:    {a['recall']['mean']:.4f} +/- {a['recall']['std']:.4f}")
    print(f"\nFull results written to {out_path.relative_to(BACKEND_DIR)}")


if __name__ == "__main__":
    main()
