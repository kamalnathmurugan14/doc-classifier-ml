from pathlib import Path

import pytest
from docx import Document
from fastapi.testclient import TestClient
from reportlab.pdfgen import canvas

from app.config import Settings
from app.main import create_app


def make_pdf(path: Path, pages: list[str]) -> None:
    c = canvas.Canvas(str(path))
    for text in pages:
        y = 800
        for line in text.split("\n"):
            c.drawString(50, y, line)
            y -= 16
        c.showPage()
    c.save()


def make_docx(path: Path, paragraphs: list[str]) -> None:
    d = Document()
    for p in paragraphs:
        d.add_paragraph(p)
    d.save(str(path))


INVOICE = (
    "INVOICE\nInvoice number: INV-1042\nBill to: Acme Corp\nSubtotal: $900.00\nGST: $100.00\n"
    "Total due: $1000.00\nDue date: 2026-01-31"
)
CONTRACT = (
    "SERVICE AGREEMENT\nThis agreement is made between the parties. The renewal of this contract happens "
    "yearly. Governing law applies. The party agrees to keep all terms confidential."
)


@pytest.fixture
def docs(tmp_path: Path) -> Path:
    root = tmp_path / "docs"
    (root / "sub").mkdir(parents=True)
    make_pdf(root / "invoice.pdf", [INVOICE])
    make_docx(root / "contract.docx", CONTRACT.split(". "))
    (root / "garage.txt").write_text("The automobile was repaired at the garage last week.", encoding="utf-8")
    (root / "notes.md").write_text(
        "# Notes\n\nQuarterly report: executive summary, findings, conclusion and recommendations.", encoding="utf-8"
    )
    (root / "sub" / "recipe.txt").write_text("Mix flour and eggs. Bake for thirty minutes.", encoding="utf-8")
    return root


@pytest.fixture
def settings(tmp_path: Path, docs: Path) -> Settings:
    return Settings(docs_root=docs, data_dir=tmp_path / "data", max_upload_mb=1, min_docs_per_class=5, _env_file=None)


@pytest.fixture
def client(settings: Settings):
    with TestClient(create_app(settings)) as c:
        yield c


@pytest.fixture
def trained(client):
    """Client with a synthetic dataset generated and all three algorithms trained."""
    client.post("/datasets/synthetic", json={"per_class": 12})
    run_id = client.app.state.container.trainer.run_blocking()
    return client, run_id
