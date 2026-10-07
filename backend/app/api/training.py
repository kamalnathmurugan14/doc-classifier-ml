import json

from fastapi import APIRouter, Request
from pydantic import BaseModel

from app.db.session import connect
from app.errors import AppError

router = APIRouter(prefix="/train")


class TrainIn(BaseModel):
    algos: list[str] | None = None
    test_size: float | None = None


@router.post("", status_code=202)
def train(request: Request, body: TrainIn | None = None) -> dict:
    body = body or TrainIn()
    return {"run_id": request.app.state.container.trainer.start(body.algos, body.test_size)}


@router.get("/{run_id}")
def run_status(request: Request, run_id: int) -> dict:
    s = request.app.state.container.settings
    with connect(s.db_path) as con:
        run = con.execute("SELECT * FROM training_runs WHERE id=?", (run_id,)).fetchone()
        if run is None:
            raise AppError("NOT_FOUND", "Training run not found", 404)
        models = con.execute(
            "SELECT id, algo, version, accuracy, macro_f1, is_active, report_json FROM models WHERE run_id=? ORDER BY id",
            (run_id,),
        ).fetchall()
    out = {
        k: run[k]
        for k in (
            "id",
            "status",
            "progress",
            "started_at",
            "finished_at",
            "n_train",
            "n_test",
            "best_model_name",
            "error",
        )
    }
    out["params"] = json.loads(run["params_json"])
    out["models"] = []
    for m in models:
        rep = json.loads(m["report_json"])
        out["models"].append(
            {
                "id": m["id"],
                "algo": m["algo"],
                "label": rep.get("algo_label"),
                "version": m["version"],
                "accuracy": m["accuracy"],
                "macro_f1": m["macro_f1"],
                "is_active": bool(m["is_active"]),
                "cv_mean": rep.get("cv_mean"),
                "cv_std": rep.get("cv_std"),
                "train_seconds": rep.get("train_seconds"),
                "overfit": rep.get("overfit"),
            }
        )
    return out
