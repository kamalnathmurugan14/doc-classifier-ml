"""Throw-away backend for Playwright: temp docs folder + data dir, served on :8000."""

import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import uvicorn  # noqa: E402

from app.config import Settings  # noqa: E402
from app.main import create_app  # noqa: E402

tmp = Path(tempfile.mkdtemp())
(tmp / "docs").mkdir()
(tmp / "docs" / "mystery.txt").write_text(
    "INVOICE Bill to: Acme Subtotal: $900 Tax: $100 Total due: $1000 Payment due 2026-01-31", encoding="utf-8"
)
uvicorn.run(
    create_app(Settings(docs_root=tmp / "docs", data_dir=tmp / "data", _env_file=None)),
    host="127.0.0.1",
    port=8000,
    log_level="warning",
)
