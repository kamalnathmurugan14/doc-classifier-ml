"""Explain a model: top words per class (global) and the words behind one prediction (local)."""

import numpy as np
from sklearn.pipeline import Pipeline


def class_weights(pipe: Pipeline) -> np.ndarray:
    """(n_classes, n_features) matrix: how strongly each word pushes towards each class."""
    clf = pipe.named_steps["clf"]
    n_classes = len(clf.classes_)
    if hasattr(clf, "calibrated_classifiers_"):  # calibrated LinearSVC: average the underlying linear models
        coef = np.mean([c.estimator.coef_ for c in clf.calibrated_classifiers_], axis=0)
    elif hasattr(clf, "coef_"):
        coef = clf.coef_
    else:  # Naive Bayes: log P(word|class) minus its average over classes
        lp = clf.feature_log_prob_
        return lp - lp.mean(axis=0, keepdims=True)
    if n_classes == 2 and coef.shape[0] == 1:  # binary linear models store a single row
        coef = np.vstack([-coef[0], coef[0]])
    return coef


def top_features(pipe: Pipeline, k: int = 10) -> dict[str, list[dict]]:
    vocab = np.array(pipe.named_steps["tfidf"].get_feature_names_out())
    w = class_weights(pipe)
    out = {}
    for i, cls in enumerate(pipe.named_steps["clf"].classes_):
        idx = np.argsort(-w[i])[:k]
        out[str(cls)] = [{"word": str(vocab[j]), "weight": round(float(w[i][j]), 4)} for j in idx]
    return out


def explain_prediction(pipe: Pipeline, text: str, class_name: str, k: int = 8) -> list[dict]:
    """Words in THIS document that contributed most to `class_name` (tf-idf value x class weight)."""
    vec = pipe.named_steps["tfidf"].transform([text])
    classes = list(pipe.named_steps["clf"].classes_)
    w = class_weights(pipe)[classes.index(class_name)]
    vocab = pipe.named_steps["tfidf"].get_feature_names_out()
    row = vec.tocoo()
    contrib = sorted(((float(v * w[j]), str(vocab[j])) for j, v in zip(row.col, row.data)), reverse=True)[:k]
    return [{"word": word, "contribution": round(c, 4)} for c, word in contrib if c > 0]
