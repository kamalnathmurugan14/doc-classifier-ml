import re
import sqlite3

from fastapi import APIRouter, Request
from pydantic import BaseModel, Field

from app.db.session import connect
from app.errors import AppError

router = APIRouter(prefix="/categories")
PALETTE = ["#3b6ef5", "#e08a1e", "#1f8f55", "#c0392b", "#8e44ad", "#16a0a8", "#d35498", "#7f8c8d"]


class CategoryIn(BaseModel):
    name: str = Field(min_length=1, max_length=40)
    color: str | None = Field(default=None, pattern=r"^#[0-9a-fA-F]{6}$")


@router.get("")
def list_categories(request: Request) -> dict:
    s = request.app.state.container.settings
    with connect(s.db_path) as con:
        rows = con.execute(
            "SELECT c.id, c.name, c.color, COUNT(l.id) AS count FROM categories c LEFT JOIN labels l ON l.category_id=c.id "
            "GROUP BY c.id ORDER BY c.name"
        ).fetchall()
    cats = [{**dict(r), "needs_more": r["count"] < s.min_docs_per_class} for r in rows]
    return {"categories": cats, "min_docs_per_class": s.min_docs_per_class}


@router.post("", status_code=201)
def create_category(request: Request, body: CategoryIn) -> dict:
    s = request.app.state.container.settings
    name = re.sub(r"\s+", " ", body.name).strip()
    with connect(s.db_path) as con:
        color = body.color or PALETTE[con.execute("SELECT COUNT(*) FROM categories").fetchone()[0] % len(PALETTE)]
        try:
            cur = con.execute("INSERT INTO categories(name, color) VALUES(?,?)", (name, color))
        except sqlite3.IntegrityError as exc:
            raise AppError("CATEGORY_EXISTS", f"Category '{name}' already exists", 409) from exc
    return {"id": cur.lastrowid, "name": name, "color": color}


@router.delete("/{category_id}", status_code=204)
def delete_category(request: Request, category_id: int) -> None:
    s = request.app.state.container.settings
    with connect(s.db_path) as con:
        if con.execute("DELETE FROM categories WHERE id=?", (category_id,)).rowcount == 0:
            raise AppError("NOT_FOUND", "Category not found", 404)
