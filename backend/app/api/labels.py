from fastapi import APIRouter, Request
from pydantic import BaseModel

from app.core.paths import ext_of, rel_posix, safe_resolve
from app.db.session import connect
from app.errors import AppError
from app.ml.registry import now

router = APIRouter()


class LabelIn(BaseModel):
    rel_path: str
    category_id: int


def upsert_label(settings, rel_path: str, category_id: int, source: str) -> dict:
    path = safe_resolve(settings.docs_root, rel_path)
    if not path.is_file() or ext_of(path.name) not in settings.extensions:
        raise AppError("NOT_FOUND", "File not found or unsupported type", 404)
    rel = rel_posix(settings.docs_root, path)
    with connect(settings.db_path) as con:
        if con.execute("SELECT 1 FROM categories WHERE id=?", (category_id,)).fetchone() is None:
            raise AppError("CATEGORY_NOT_FOUND", "Unknown category", 404)
        con.execute(
            "INSERT INTO labels(rel_path, category_id, source, created_at) VALUES(?,?,?,?) "
            "ON CONFLICT(rel_path) DO UPDATE SET category_id=excluded.category_id, source=excluded.source, created_at=excluded.created_at",
            (rel, category_id, source, now()),
        )
        row = con.execute("SELECT id FROM labels WHERE rel_path=?", (rel,)).fetchone()
    return {"id": row["id"], "rel_path": rel, "category_id": category_id, "source": source}


@router.post("/labels", status_code=201)
def create_label(request: Request, body: LabelIn) -> dict:
    return upsert_label(request.app.state.container.settings, body.rel_path, body.category_id, "manual")


@router.get("/labels")
def list_labels(request: Request, category: str = "") -> dict:
    s = request.app.state.container.settings
    sql = "SELECT l.id, l.rel_path, l.source, c.id AS category_id, c.name AS category FROM labels l JOIN categories c ON c.id=l.category_id"
    args: tuple = ()
    if category:
        sql += " WHERE c.name=? OR CAST(c.id AS TEXT)=?"
        args = (category, category)
    with connect(s.db_path) as con:
        return {"labels": [dict(r) for r in con.execute(sql + " ORDER BY l.rel_path", args)]}


@router.delete("/labels/{label_id}", status_code=204)
def delete_label(request: Request, label_id: int) -> None:
    s = request.app.state.container.settings
    with connect(s.db_path) as con:
        if con.execute("DELETE FROM labels WHERE id=?", (label_id,)).rowcount == 0:
            raise AppError("NOT_FOUND", "Label not found", 404)
