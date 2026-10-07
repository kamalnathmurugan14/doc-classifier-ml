"""One sklearn Pipeline = TF-IDF + classifier. Saving the whole pipeline guarantees identical preprocessing at predict time."""

from sklearn.calibration import CalibratedClassifierCV
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import Pipeline
from sklearn.svm import LinearSVC

from app.core.text_cleaner import TextCleaner

ALGOS = ("logreg", "svm", "nb")
LABELS = {"logreg": "Logistic Regression", "svm": "Linear SVM (calibrated)", "nb": "Multinomial Naive Bayes"}


def build_pipeline(
    algo: str, max_features: int, ngram_range: tuple[int, int], seed: int, min_class_count: int = 5
) -> Pipeline:
    tfidf = TfidfVectorizer(
        preprocessor=TextCleaner(),
        max_features=max_features,
        ngram_range=ngram_range,
        sublinear_tf=True,  # 1 + log(tf): the 50th "invoice" counts less than 50x the first
        min_df=1,
    )
    if algo == "logreg":
        clf = LogisticRegression(max_iter=1000, random_state=seed)
    elif algo == "svm":
        # LinearSVC has no probabilities; calibration (Platt scaling via CV) adds them
        clf = CalibratedClassifierCV(LinearSVC(random_state=seed), cv=max(2, min(3, min_class_count)))
    elif algo == "nb":
        clf = MultinomialNB()
    else:
        raise ValueError(f"unknown algorithm: {algo}")
    return Pipeline([("tfidf", tfidf), ("clf", clf)])
