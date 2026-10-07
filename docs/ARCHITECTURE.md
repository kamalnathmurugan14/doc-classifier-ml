# Architecture

| Module | Responsibility |
|---|---|
| `core/paths.py`, `api/fs.py` | The only path touching disk; explorer, upload, preview |
| `core/extractors.py`, `core/text_cleaner.py` | file → text → cleaned tokens (money/date/url/email kept as tokens) |
| `ml/pipeline.py` | `Pipeline([TfidfVectorizer(preprocessor=TextCleaner), classifier])` |
| `ml/trainer.py` | load labelled text, validate, stratified split, fit each algorithm, evaluate, register, activate best |
| `ml/evaluator.py` | accuracy, macro/weighted F1, per-class report, confusion matrix, k-fold CV, overfitting flag |
| `ml/registry.py` | `models/model_v{N}_{algo}.joblib` + `models` table (version = incrementing int, sklearn/python versions stored) |
| `ml/predictor.py`, `ml/explain.py` | top-3 probabilities, *Uncertain* guard, global top words and per-prediction contributions |
| `ml/synth.py` | template-based fake documents with controllable label noise |

## Decisions
- **Cleaning lives inside the vectorizer** (`preprocessor=TextCleaner()`), so a saved pipeline accepts raw text — train/predict skew is impossible. `TextCleaner` is a frozen dataclass so it pickles.
- **Calibrated LinearSVC**: SVMs output margins, not probabilities. `CalibratedClassifierCV` (Platt scaling) gives the confidences the UI and the *Uncertain* guard need.
- **Exact duplicate texts are dropped before the split** — copies landing in both train and test inflate scores (data leakage). The run reports how many were dropped.
- **Two estimates**: held-out test split (what you report) and 5-fold CV on all data (how stable it is). Folds are capped by the smallest class.
- **Best model = highest macro-F1**, not accuracy: macro-F1 weighs every class equally, so a rare class can't hide behind a big one.
- **Feedback = a label with `source=feedback`.** Retraining creates a new version; rollback is just flipping `is_active`.
- **Training runs in a thread**; validation runs synchronously first so mistakes return an immediate 422 with an explanation.
- **Pickle safety**: artifact names come from the DB but are reduced to a basename and resolved inside `data/models`.
