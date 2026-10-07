import json

from fastapi import APIRouter, Request
from pydantic import BaseModel

from app.api.labels import upsert_label
from app.core.paths import ext_of, is_inside, rel_posix, safe_resolve
from app.db.session import connect
from app.errors import AppError

router = APIRouter()


class PredictIn(BaseModel):
    rel_path: str


class FolderIn(BaseModel):
    path: str = ""


class FeedbackIn(BaseModel):
    rel_path: str
    correct_category_id: int


@router.post("/predict")
def predict(request: Request, body: PredictIn) -> dict:
    return request.app.state.container.predictor.predict_file(body.rel_path)


@router.post("/predict-folder", status_code=202)
def predict_folder(request: Request, body: FolderIn | None = None) -> dict:
    c = request.app.state.container
    if c.registry.active() is None:
        raise AppError("NO_ACTIVE_MODEL", "No trained model yet. Label some documents and train first.", 409)
    root = safe_resolve(c.settings.docs_root, body.path if body else "")
    if not root.is_dir():
        raise AppError("NOT_FOUND", "Folder not found", 404)
    files = [
        rel_posix(c.settings.docs_root, p)
        for p in sorted(root.rglob("*"))
        if p.is_file()
        and is_inside(root, p)
        and ext_of(p.name) in c.settings.extensions
        and not any(x.startswith(".") for x in p.relative_to(root).parts)
    ]
    return {"job_id": c.start_folder_job(files), "total": len(files)}


@router.get("/predict-folder/{job_id}")
def folder_status(request: Request, job_id: str) -> dict:
    job = request.app.state.container.folder_jobs.get(job_id)
    if job is None:
        raise AppError("NOT_FOUND", "Unknown job", 404)
    return {k: v for k, v in job.items() if k != "thread"}


@router.get("/predictions")
def history(request: Request, rel_path: str = "") -> dict:
    s = request.app.state.container.settings
    with connect(s.db_path) as con:
        rows = con.execute(
            "SELECT * FROM predictions WHERE (?='' OR rel_path=?) ORDER BY id DESC LIMIT 100", (rel_path, rel_path)
        ).fetchall()
    return {
        "predictions": [
            {
                "rel_path": r["rel_path"],
                "model_id": r["model_id"],
                "top3": json.loads(r["top3_json"]),
                "created_at": r["created_at"],
            }
            for r in rows
        ]
    }


@router.post("/feedback", status_code=201)
def feedback(request: Request, body: FeedbackIn) -> dict:
    """A user correction becomes a new label (source=feedback); retrain to learn from it."""
    return upsert_label(request.app.state.container.settings, body.rel_path, body.correct_category_id, "feedback")
