import json

from fastapi import APIRouter, Request
from fastapi.responses import PlainTextResponse

from app.db.session import connect
from app.errors import AppError

router = APIRouter(prefix="/models")


@router.get("")
def list_models(request: Request) -> dict:
    s = request.app.state.container.settings
    with connect(s.db_path) as con:
        rows = con.execute(
            "SELECT id, run_id, algo, version, accuracy, macro_f1, is_active, created_at FROM models ORDER BY version DESC"
        ).fetchall()
    return {"models": [{**dict(r), "is_active": bool(r["is_active"])} for r in rows]}


@router.get("/{model_id}/metrics")
def metrics(request: Request, model_id: int) -> dict:
    s = request.app.state.container.settings
    with connect(s.db_path) as con:
        r = con.execute("SELECT * FROM models WHERE id=?", (model_id,)).fetchone()
    if r is None:
        raise AppError("MODEL_NOT_FOUND", "Unknown model id", 404)
    rep = json.loads(r["report_json"])
    return {
        "id": r["id"],
        "algo": r["algo"],
        "version": r["version"],
        "is_active": bool(r["is_active"]),
        "created_at": r["created_at"],
        "accuracy": r["accuracy"],
        "macro_f1": r["macro_f1"],
        "metrics": rep,
        "top_features": json.loads(r["top_features_json"]),
    }


@router.post("/{model_id}/activate")
def activate(request: Request, model_id: int) -> dict:
    request.app.state.container.registry.activate(model_id)
    return {"active": model_id}


@router.get("/{model_id}/card", response_class=PlainTextResponse)
def model_card(request: Request, model_id: int) -> str:
    """Bonus: a markdown model card (what it is, how it scored, known limits)."""
    m = metrics(request, model_id)
    x = m["metrics"]
    rows = "\n".join(
        f"| {r['class']} | {r['precision']:.2f} | {r['recall']:.2f} | {r['f1']:.2f} | {r['support']} |"
        for r in x["per_class"]
    )
    cv = "n/a" if x["cv_mean"] is None else f"{x['cv_mean']:.3f} ± {x['cv_std']:.3f} ({x['cv_folds']}-fold)"
    return (
        f"# Model card — v{m['version']} ({x['algo_label']})\n\n"
        f"- Created: {m['created_at']}  \n- scikit-learn {x['meta']['sklearn']}, Python {x['meta']['python']}\n"
        f"- Features: TF-IDF (sublinear tf) on cleaned text\n\n"
        f"## Results (held-out test set)\n\n- Accuracy: {m['accuracy']:.3f}\n- Macro F1: {m['macro_f1']:.3f}\n- Cross-validated macro F1: {cv}\n"
        f"- Train accuracy: {x['train_accuracy']:.3f}{' (**possible overfitting**)' if x['overfit'] else ''}\n\n"
        f"| class | precision | recall | F1 | support |\n|---|---|---|---|---|\n{rows}\n\n"
        "## Intended use & limits\n\nClassifies text documents into the categories it was trained on. Predictions below the "
        "confidence threshold are reported as *Uncertain*. Quality depends on the amount and balance of labelled data; scanned "
        "PDFs without text cannot be classified.\n"
    )
