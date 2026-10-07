"""Prediction with the active model: top-3 categories + confidence + 'Uncertain' guard + word-level explanation."""

import json

from app.config import Settings
from app.core.extractors import extract
from app.core.paths import rel_posix, safe_resolve
from app.db.session import connect
from app.errors import AppError
from app.ml.explain import explain_prediction
from app.ml.registry import Registry, now


class Predictor:
    def __init__(self, settings: Settings, registry: Registry) -> None:
        self.s, self.registry = settings, registry

    def predict_text(self, text: str) -> tuple[dict, dict]:
        active = self.registry.active()
        if active is None:
            raise AppError("NO_ACTIVE_MODEL", "No trained model yet. Label some documents and train first.", 409)
        pipe = self.registry.load(active["id"])
        proba = pipe.predict_proba([text])[0]
        order = proba.argsort()[::-1][:3]
        classes = pipe.named_steps["clf"].classes_
        top3 = [{"category": str(classes[i]), "confidence": round(float(proba[i]), 4)} for i in order]
        uncertain = top3[0]["confidence"] < self.s.uncertain_below
        words = explain_prediction(pipe, text, top3[0]["category"])
        return {"predictions": top3, "uncertain": uncertain, "top_words": words, "model_id": active["id"]}, active

    def predict_file(self, rel_path: str) -> dict:
        path = safe_resolve(self.s.docs_root, rel_path)
        if not path.is_file() or path.suffix.lower().lstrip(".") not in self.s.extensions:
            raise AppError("NOT_FOUND", "File not found", 404)
        try:
            text = extract(path).text
        except Exception as exc:  # noqa: BLE001
            raise AppError("EXTRACT_FAILED", f"Cannot read this file: {type(exc).__name__}", 422) from exc
        if not text.strip():
            raise AppError("NO_TEXT", "This file has no extractable text", 422)
        result, active = self.predict_text(text)
        rel = rel_posix(self.s.docs_root, path)
        with connect(self.s.db_path) as con:
            con.execute(
                "INSERT INTO predictions(rel_path, model_id, top3_json, created_at) VALUES(?,?,?,?)",
                (rel, active["id"], json.dumps(result["predictions"]), now()),
            )
        return {"rel_path": rel, **result}
