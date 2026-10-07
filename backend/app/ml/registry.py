"""Model registry: joblib artifacts on disk + metadata rows in SQLite. Version = incrementing integer."""

import json
import platform
import sys
from datetime import UTC, datetime
from pathlib import Path

import joblib
import sklearn

from app.config import Settings
from app.db.session import connect
from app.errors import AppError


def now() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds")


class Registry:
    def __init__(self, settings: Settings) -> None:
        self.s = settings
        settings.models_dir.mkdir(parents=True, exist_ok=True)
        self._cache: dict[int, object] = {}

    def save(self, run_id: int, algo: str, pipe, metrics: dict, top_features: dict) -> int:
        with connect(self.s.db_path) as con:
            version = (con.execute("SELECT COALESCE(MAX(version),0) FROM models").fetchone()[0]) + 1
            path = self.s.models_dir / f"model_v{version}_{algo}.joblib"
            joblib.dump(pipe, path)
            metrics = {
                **metrics,
                "meta": {
                    "sklearn": sklearn.__version__,
                    "python": sys.version.split()[0],
                    "platform": platform.system(),
                },
            }
            cur = con.execute(
                "INSERT INTO models(run_id,algo,version,accuracy,macro_f1,report_json,confusion_json,top_features_json,artifact_path,created_at)"
                " VALUES(?,?,?,?,?,?,?,?,?,?)",
                (
                    run_id,
                    algo,
                    version,
                    metrics["accuracy"],
                    metrics["macro_f1"],
                    json.dumps(metrics),
                    json.dumps(metrics["confusion"]),
                    json.dumps(top_features),
                    path.name,
                    now(),
                ),
            )
            return int(cur.lastrowid)

    def activate(self, model_id: int) -> None:
        with connect(self.s.db_path) as con:
            if con.execute("SELECT 1 FROM models WHERE id=?", (model_id,)).fetchone() is None:
                raise AppError("MODEL_NOT_FOUND", "Unknown model id", 404)
            con.execute("UPDATE models SET is_active=0")
            con.execute("UPDATE models SET is_active=1 WHERE id=?", (model_id,))

    def active(self) -> dict | None:
        with connect(self.s.db_path) as con:
            row = con.execute("SELECT * FROM models WHERE is_active=1").fetchone()
        return dict(row) if row else None

    def load(self, model_id: int):
        if model_id not in self._cache:
            with connect(self.s.db_path) as con:
                row = con.execute("SELECT artifact_path FROM models WHERE id=?", (model_id,)).fetchone()
            if row is None:
                raise AppError("MODEL_NOT_FOUND", "Unknown model id", 404)
            path = self.s.models_dir / Path(row["artifact_path"]).name  # basename only: never trust DB paths blindly
            if not path.exists():
                raise AppError("MODEL_FILE_MISSING", "Model file is missing on disk; retrain", 500)
            self._cache[model_id] = joblib.load(path)
        return self._cache[model_id]
