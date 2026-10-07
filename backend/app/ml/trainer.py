"""Training: load labelled text -> validate -> stratified split -> fit each algorithm -> evaluate -> register best."""

import json
import logging
import threading
import time
from dataclasses import dataclass
from functools import partial

from sklearn.model_selection import train_test_split

from app.config import Settings
from app.core.extractors import extract
from app.core.paths import safe_resolve
from app.db.session import connect
from app.errors import AppError
from app.ml.evaluator import cross_validate, evaluate
from app.ml.explain import top_features
from app.ml.pipeline import ALGOS, LABELS, build_pipeline
from app.ml.registry import Registry, now

log = logging.getLogger(__name__)


@dataclass
class Dataset:
    texts: list[str]
    labels: list[str]
    paths: list[str]
    missing: list[str]
    duplicates_dropped: int


def load_dataset(s: Settings) -> Dataset:
    """Read every labelled file. Exact-duplicate texts are dropped: copies in both train and test = data leakage."""
    texts, labels, paths, missing, seen, dupes = [], [], [], [], set(), 0
    with connect(s.db_path) as con:
        rows = con.execute(
            "SELECT l.rel_path, c.name FROM labels l JOIN categories c ON c.id=l.category_id ORDER BY l.id"
        ).fetchall()
    for r in rows:
        try:
            text = extract(safe_resolve(s.docs_root, r["rel_path"])).text
        except Exception:  # noqa: BLE001 - deleted or unreadable file
            missing.append(r["rel_path"])
            continue
        if not text.strip():
            missing.append(r["rel_path"])
            continue
        key = hash(text)
        if key in seen:
            dupes += 1
            continue
        seen.add(key)
        texts.append(text)
        labels.append(r["name"])
        paths.append(r["rel_path"])
    return Dataset(texts, labels, paths, missing, dupes)


def validate(ds: Dataset, min_per_class: int) -> dict[str, int]:
    counts: dict[str, int] = {}
    for y in ds.labels:
        counts[y] = counts.get(y, 0) + 1
    if len(counts) < 2:
        raise AppError(
            "NOT_ENOUGH_CLASSES", f"Need at least 2 categories with labelled documents (found {len(counts)}).", 422
        )
    low = {k: v for k, v in counts.items() if v < min_per_class}
    if low:
        detail = ", ".join(f"{k}: {v}" for k, v in sorted(low.items()))
        raise AppError(
            "NOT_ENOUGH_DOCS",
            f"Each category needs at least {min_per_class} readable, unique documents. Too few -> {detail}.",
            422,
        )
    return counts


class Trainer:
    def __init__(self, settings: Settings, registry: Registry) -> None:
        self.s, self.registry = settings, registry
        self.thread: threading.Thread | None = None

    def start(self, algos: list[str] | None, test_size: float | None) -> int:
        algos = algos or list(ALGOS)
        bad = [a for a in algos if a not in ALGOS]
        if bad:
            raise AppError("BAD_ALGO", f"Unknown algorithm(s): {', '.join(bad)}. Choose from {', '.join(ALGOS)}", 422)
        ts = test_size if test_size is not None else self.s.test_size
        if not 0.05 <= ts <= 0.5:
            raise AppError("BAD_TEST_SIZE", "test_size must be between 0.05 and 0.5", 422)
        ds = load_dataset(self.s)  # validate synchronously so the user gets a 422 immediately
        counts = validate(ds, self.s.min_docs_per_class)
        with connect(self.s.db_path) as con:
            if con.execute("SELECT 1 FROM training_runs WHERE status='running'").fetchone():
                raise AppError("TRAINING_RUNNING", "A training run is already in progress", 409)
            run_id = con.execute(
                "INSERT INTO training_runs(started_at, progress, params_json) VALUES(?,?,?)",
                (
                    now(),
                    "starting",
                    json.dumps(
                        {
                            "algos": algos,
                            "test_size": ts,
                            "class_counts": counts,
                            "missing_files": ds.missing,
                            "duplicates_dropped": ds.duplicates_dropped,
                        }
                    ),
                ),
            ).lastrowid
        self.thread = threading.Thread(target=self._run, args=(run_id, algos, ts, ds), daemon=True)
        self.thread.start()
        return run_id

    def run_blocking(self, algos: list[str] | None = None, test_size: float | None = None) -> int:
        run_id = self.start(algos, test_size)
        assert self.thread is not None
        self.thread.join()
        return run_id

    def _progress(self, run_id: int, msg: str) -> None:
        with connect(self.s.db_path) as con:
            con.execute("UPDATE training_runs SET progress=? WHERE id=?", (msg, run_id))

    def _run(self, run_id: int, algos: list[str], test_size: float, ds: Dataset) -> None:
        try:
            X_tr, X_te, y_tr, y_te = train_test_split(
                ds.texts, ds.labels, test_size=test_size, stratify=ds.labels, random_state=self.s.random_seed
            )
            min_count = min(y_tr.count(c) for c in set(y_tr))
            best_name, best_f1, best_id = "", -1.0, 0
            for i, algo in enumerate(algos, 1):
                self._progress(run_id, f"training {LABELS[algo]} ({i}/{len(algos)})")
                make = partial(build_pipeline, algo, self.s.max_features, self.s.ngrams, self.s.random_seed, min_count)
                t0 = time.perf_counter()
                pipe = make().fit(X_tr, y_tr)
                fit_s = time.perf_counter() - t0
                metrics = evaluate(pipe, X_tr, y_tr, X_te, y_te)
                metrics.update(cross_validate(make, ds.texts, ds.labels, self.s.random_seed))
                metrics["train_seconds"] = round(fit_s, 3)
                metrics["algo_label"] = LABELS[algo]
                model_id = self.registry.save(run_id, algo, pipe, metrics, top_features(pipe))
                if metrics["macro_f1"] > best_f1:
                    best_name, best_f1, best_id = algo, metrics["macro_f1"], model_id
            self.registry.activate(best_id)  # best macro-F1 wins
            with connect(self.s.db_path) as con:
                con.execute(
                    "UPDATE training_runs SET status='done', finished_at=?, progress='done', n_train=?, n_test=?, best_model_name=? WHERE id=?",
                    (now(), len(X_tr), len(X_te), best_name, run_id),
                )
        except Exception as exc:  # noqa: BLE001
            log.exception("training_failed")
            with connect(self.s.db_path) as con:
                con.execute(
                    "UPDATE training_runs SET status='failed', finished_at=?, error=?, progress='failed' WHERE id=?",
                    (now(), f"{type(exc).__name__}: {exc}"[:400], run_id),
                )
