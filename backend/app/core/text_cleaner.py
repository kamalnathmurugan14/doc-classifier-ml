"""Text cleaning. Lives inside the sklearn Pipeline so training and prediction preprocess identically."""

import re
from dataclasses import dataclass

_URL = re.compile(r"https?://\S+|www\.\S+")
_EMAIL = re.compile(r"\b[\w.+-]+@[\w-]+\.[\w.]+\b")
_MONEY = re.compile(
    r"(?:[$€£₹]|rs\.?|usd|inr)\s?\d[\d,]*(?:\.\d+)?|\d[\d,]*(?:\.\d+)?\s?(?:usd|inr|dollars|rupees)", re.I
)
_DATE = re.compile(r"\b\d{4}[-/]\d{1,2}[-/]\d{1,2}\b|\b\d{1,2}[-/]\d{1,2}[-/]\d{2,4}\b")
_NUMBER = re.compile(r"\b\d+\b")
_PUNCT = re.compile(r"[^a-z_\s]")
_SPACE = re.compile(r"\s+")
STOPWORDS = frozenset(
    "a an and are as at be by for from in is it of on or that the to was were will with this these those".split()
)


@dataclass(frozen=True)
class TextCleaner:
    """Callable + picklable (joblib stores it inside the saved pipeline)."""

    remove_numbers: bool = True
    remove_stopwords: bool = False

    def __call__(self, text: str) -> str:
        t = text.lower()
        t = _URL.sub(" urltoken ", t)
        t = _EMAIL.sub(" emailtoken ", t)
        t = _MONEY.sub(" moneytoken ", t)  # money amounts are a strong signal for invoices - keep them as a token
        t = _DATE.sub(" datetoken ", t)
        if self.remove_numbers:
            t = _NUMBER.sub(" ", t)
        t = _PUNCT.sub(" ", t)
        words = _SPACE.sub(" ", t).strip().split(" ")
        if self.remove_stopwords:
            words = [w for w in words if w not in STOPWORDS]
        return " ".join(w for w in words if w)


clean_text = TextCleaner()
