import pickle

from app.core.text_cleaner import TextCleaner, clean_text


def test_cleaner_keeps_money_and_dates_as_tokens():
    out = clean_text("Total due: $1,250.50 by 2026-01-31, see https://x.io or mail a@b.com. 42 items")
    assert "moneytoken" in out and "datetoken" in out and "urltoken" in out and "emailtoken" in out
    assert "42" not in out and "1250" not in out and "https" not in out


def test_cleaner_options_and_pickle():
    assert "the" not in TextCleaner(remove_stopwords=True)("the invoice").split()
    c = pickle.loads(pickle.dumps(TextCleaner(remove_stopwords=True)))
    assert c("The Invoice") == "invoice"


def test_category_crud_and_duplicates(client):
    r = client.post("/categories", json={"name": "Invoice"})
    assert r.status_code == 201
    cid = r.json()["id"]
    assert client.post("/categories", json={"name": "Invoice"}).status_code == 409
    assert client.post("/categories", json={"name": ""}).status_code == 422
    cats = client.get("/categories").json()
    assert cats["categories"][0]["count"] == 0 and cats["categories"][0]["needs_more"] is True
    assert client.delete(f"/categories/{cid}").status_code == 204
    assert client.delete(f"/categories/{cid}").status_code == 404


def test_label_upsert_list_delete(client):
    a = client.post("/categories", json={"name": "A"}).json()["id"]
    b = client.post("/categories", json={"name": "B"}).json()["id"]
    lab = client.post("/labels", json={"rel_path": "garage.txt", "category_id": a}).json()
    client.post("/labels", json={"rel_path": "garage.txt", "category_id": b})  # relabel = update, not duplicate
    rows = client.get("/labels").json()["labels"]
    assert len(rows) == 1 and rows[0]["category"] == "B"
    assert len(client.get("/labels", params={"category": "A"}).json()["labels"]) == 0
    assert len(client.get("/labels", params={"category": "B"}).json()["labels"]) == 1
    assert client.delete(f"/labels/{lab['id']}").status_code == 204
    assert client.delete(f"/labels/{lab['id']}").status_code == 404


def test_label_validation(client):
    a = client.post("/categories", json={"name": "A"}).json()["id"]
    assert client.post("/labels", json={"rel_path": "../../etc/passwd", "category_id": a}).status_code == 400
    assert client.post("/labels", json={"rel_path": "missing.txt", "category_id": a}).status_code == 404
    assert (
        client.post("/labels", json={"rel_path": "garage.txt", "category_id": 999}).json()["error"]["code"]
        == "CATEGORY_NOT_FOUND"
    )
