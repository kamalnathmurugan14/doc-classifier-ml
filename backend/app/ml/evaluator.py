"""Metrics: accuracy, macro/weighted F1, per-class report, confusion matrix, cross-validation, overfitting flag."""

import numpy as np
from sklearn.metrics import accuracy_score, confusion_matrix, f1_score, precision_recall_fscore_support
from sklearn.model_selection import StratifiedKFold, cross_val_score
from sklearn.pipeline import Pipeline

OVERFIT_GAP = 0.15  # train accuracy this much above test accuracy => warn


def evaluate(pipe: Pipeline, X_train: list[str], y_train: list[str], X_test: list[str], y_test: list[str]) -> dict:
    classes = [str(c) for c in pipe.named_steps["clf"].classes_]
    pred = pipe.predict(X_test)
    prec, rec, f1, sup = precision_recall_fscore_support(y_test, pred, labels=classes, zero_division=0)
    train_acc = float(accuracy_score(y_train, pipe.predict(X_train)))
    test_acc = float(accuracy_score(y_test, pred))
    return {
        "accuracy": test_acc,
        "macro_f1": float(f1_score(y_test, pred, average="macro", zero_division=0)),
        "weighted_f1": float(f1_score(y_test, pred, average="weighted", zero_division=0)),
        "train_accuracy": train_acc,
        "overfit": bool(train_acc - test_acc > OVERFIT_GAP),
        "per_class": [
            {"class": c, "precision": float(p), "recall": float(r), "f1": float(f), "support": int(s)}
            for c, p, r, f, s in zip(classes, prec, rec, f1, sup, strict=True)
        ],
        "confusion": {"labels": classes, "matrix": confusion_matrix(y_test, pred, labels=classes).tolist()},
    }


def cross_validate(make_pipe, X: list[str], y: list[str], seed: int, folds: int = 5) -> dict:
    """k-fold CV on ALL labelled data: a steadier estimate than one train/test split."""
    min_count = min(np.unique(y, return_counts=True)[1])
    k = int(min(folds, min_count))
    if k < 2:
        return {"cv_folds": 0, "cv_mean": None, "cv_std": None}
    scores = cross_val_score(
        make_pipe(), X, y, cv=StratifiedKFold(k, shuffle=True, random_state=seed), scoring="f1_macro"
    )
    return {"cv_folds": k, "cv_mean": float(scores.mean()), "cv_std": float(scores.std())}
