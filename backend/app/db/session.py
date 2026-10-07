"""Plain sqlite3 (no ORM) so the SQL is visible. One short-lived connection per operation."""

import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

SCHEMA = """
CREATE TABLE IF NOT EXISTS categories(
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT UNIQUE NOT NULL,
  color TEXT NOT NULL DEFAULT '#3b6ef5'
);
CREATE TABLE IF NOT EXISTS labels(
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  rel_path TEXT UNIQUE NOT NULL,
  category_id INTEGER NOT NULL REFERENCES categories(id) ON DELETE CASCADE,
  source TEXT NOT NULL DEFAULT 'manual' CHECK(source IN ('manual','feedback','synthetic')),
  created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS training_runs(
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  started_at TEXT NOT NULL,
  finished_at TEXT,
  status TEXT NOT NULL DEFAULT 'running',     -- running | done | failed
  progress TEXT,
  params_json TEXT NOT NULL DEFAULT '{}',
  n_train INTEGER, n_test INTEGER,
  best_model_name TEXT,
  error TEXT
);
CREATE TABLE IF NOT EXISTS models(
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  run_id INTEGER NOT NULL REFERENCES training_runs(id) ON DELETE CASCADE,
  algo TEXT NOT NULL,
  version INTEGER NOT NULL,
  accuracy REAL, macro_f1 REAL,
  report_json TEXT, confusion_json TEXT, top_features_json TEXT,
  artifact_path TEXT NOT NULL,
  is_active INTEGER NOT NULL DEFAULT 0,
  created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS predictions(
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  rel_path TEXT NOT NULL,
  model_id INTEGER NOT NULL REFERENCES models(id) ON DELETE CASCADE,
  top3_json TEXT NOT NULL,
  created_at TEXT NOT NULL
);
"""


def init_db(db_path: Path) -> None:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    with connect(db_path) as con:
        con.executescript(SCHEMA)


@contextmanager
def connect(db_path: Path) -> Iterator[sqlite3.Connection]:
    con = sqlite3.connect(db_path, timeout=30)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA foreign_keys=ON")
    try:
        yield con
        con.commit()
    finally:
        con.close()
