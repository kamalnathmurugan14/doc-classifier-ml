from fastapi import APIRouter, Request
from pydantic import BaseModel, Field

from app.db.session import connect
from app.ml import synth
from app.ml.registry import now

router = APIRouter(prefix="/datasets")


class SynthIn(BaseModel):
    per_class: int = Field(default=20, ge=1, le=200)
    noise: float = Field(default=0.1, ge=0, le=0.5)


@router.post("/synthetic", status_code=201)
def make_synthetic(request: Request, body: SynthIn | None = None) -> dict:
    body = body or SynthIn()
    s = request.app.state.container.settings
    made = synth.generate(s.docs_root, body.per_class, s.random_seed, body.noise)
    with connect(s.db_path) as con:
        ids = {}
        for cls in synth.CLASSES:
            con.execute("INSERT OR IGNORE INTO categories(name) VALUES(?)", (cls,))
            ids[cls] = con.execute("SELECT id FROM categories WHERE name=?", (cls,)).fetchone()["id"]
        con.executemany(
            "INSERT INTO labels(rel_path, category_id, source, created_at) VALUES(?,?,?,?) "
            "ON CONFLICT(rel_path) DO UPDATE SET category_id=excluded.category_id, source='synthetic'",
            [(rel, ids[cls], "synthetic", now()) for rel, cls in made],
        )
    return {"generated": len(made), "per_class": body.per_class, "folder": "_synthetic"}
