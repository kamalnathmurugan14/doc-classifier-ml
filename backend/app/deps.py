"""Wires services together."""

import threading
import uuid

from app.config import Settings
from app.db.session import init_db
from app.ml.predictor import Predictor
from app.ml.registry import Registry
from app.ml.trainer import Trainer


class Container:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        settings.docs_root.mkdir(parents=True, exist_ok=True)
        init_db(settings.db_path)
        self.registry = Registry(settings)
        self.trainer = Trainer(settings, self.registry)
        self.predictor = Predictor(settings, self.registry)
        self.folder_jobs: dict[str, dict] = {}
        self._lock = threading.Lock()

    def start_folder_job(self, rel_paths: list[str]) -> str:
        job_id = uuid.uuid4().hex[:12]
        self.folder_jobs[job_id] = {"state": "running", "done": 0, "total": len(rel_paths), "results": [], "errors": []}

        def work() -> None:
            job = self.folder_jobs[job_id]
            for rel in rel_paths:
                try:
                    job["results"].append(self.predictor.predict_file(rel))
                except Exception as exc:  # noqa: BLE001
                    job["errors"].append({"rel_path": rel, "error": getattr(exc, "message", str(exc))})
                job["done"] += 1
            job["state"] = "done"

        t = threading.Thread(target=work, daemon=True)
        t.start()
        self.folder_jobs[job_id]["thread"] = t
        return job_id
