# Learning notes

## ML concepts (read this first)
- **Features vs labels** — features are what the model sees (word weights); the label is the answer you provide (the category).
- **TF-IDF** — *term frequency* × *inverse document frequency*. A word is important if it appears often in this document and rarely across all documents. "total" in every invoice is useful; "the" is not. `sublinear_tf` uses `1 + log(tf)` so repetition has diminishing returns.
- **Train/test split** — the model is only graded on documents it has never seen. Grading on training data measures memory, not learning.
- **Cross-validation** — repeat the split k times so one lucky split doesn't mislead you. The ± in "85 % ± 2" is how much the score moves between folds.
- **Overfitting / underfitting** — overfit: train ≫ test (the model memorised). Underfit: both low (too simple or too few features). The Metrics page flags train−test > 15 points.
- **Precision / recall / F1** — precision: of the documents I called *Invoice*, how many were? Recall: of all real invoices, how many did I find? F1 is their harmonic mean. Macro-F1 averages classes equally; weighted-F1 by size.
- **Class imbalance** — 95 "Other" + 5 "Invoice" gives 95 % accuracy for "always Other". Accuracy lies; look at per-class recall and macro-F1.
- **Calibration** — a model saying "90 %" should be right ~90 % of the time. SVM margins aren't probabilities until calibrated.
- **Data leakage** — information from the test set sneaking into training: duplicates in both splits, fitting TF-IDF on all data before splitting, labels derived from the file name. We drop duplicates and fit the vectorizer *inside* the pipeline (only on train data).
- **More labelled data helps** — compare 5 vs 20 documents per class and watch CV scores rise and tighten.

## Milestones
**M0 Scaffold** — config/health/CI. *Mistake:* parsing `NGRAM_RANGE` ad hoc in several places; centralised in `Settings.ngrams`.
**M1 Safe FS** — see project 1; added `/fs/preview` for the Label page.
**M2 Extractors + cleaner** — *Concept:* cleaning choices change features. Money/dates become tokens (`moneytoken`) because "$1,250.50" is an invoice clue but every amount is a different string. *Try:* turn `remove_numbers` off and see what changes.
**M3 Categories + labels** — upsert on `rel_path` (a file has one label). *Try:* relabel a file and watch the counter update.
**M4 Synthetic data** — fake documents from templates with `noise` (lines borrowed from other classes). *Mistake:* the first generator produced exact-duplicate "Other" documents — a tiny real-world leakage lesson; added a unique reference line.
**M5 One algorithm** — *Concept:* Pipeline = one object for preprocessing + model. *Try:* print `pipe.named_steps["tfidf"].get_feature_names_out()[:20]`.
**M6 Multi-algo + registry** — *Concept:* compare models on the same split and select by macro-F1; keep every version. *Try:* train with `test_size=0.5` and watch variance grow.
**M7 Metrics UI** — read the confusion matrix row by row (true class) to see which categories get confused; check top words make sense (if "datetoken" is the top word for Contracts, your data is biased).
**M8 Prediction** — top-3 + *Uncertain* below `UNCERTAIN_BELOW`. *Try:* classify a recipe; it should be Other or Uncertain.
**M9 Feedback loop** — corrections become labels, retrain creates v+1, rollback activates an old version. *Common mistake:* forgetting to retrain after feedback.
**M10 Polish** — model card export (`GET /models/{id}/card`), docs, Playwright smoke test.
