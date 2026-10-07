# 5-step demo script
1. **Data** – Label page → *Generate synthetic dataset*; show the category counters (20 each) and preview/relabel one file.
2. **Train** – Train page → keep all three algorithms → *Train*; point at the comparison table (accuracy, macro-F1, CV ±, time) and the "best" badge.
3. **Understand** – Metrics page → confusion matrix, per-class precision/recall, top words per class.
4. **Predict** – Predict page → click a document (top-3 bars, words that drove it), then *Classify whole folder*.
5. **Improve** – Correct a wrong/uncertain prediction (*Wrong? Correct it*), retrain, then use Models → *Activate / roll back* to compare versions; `GET /models/{id}/card` for the model card.
