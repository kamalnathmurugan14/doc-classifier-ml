from app.ml import synth


def test_synthetic_5_classes_x_20_generated_and_labelled(client, docs):
    r = client.post("/datasets/synthetic", json={"per_class": 20}).json()
    assert r["generated"] == 100
    cats = {c["name"]: c["count"] for c in client.get("/categories").json()["categories"]}
    assert cats == {"Contract": 20, "Invoice": 20, "Other": 20, "Report": 20, "Resume": 20}
    assert len(list((docs / "_synthetic").rglob("*.txt"))) == 100
    assert {x["source"] for x in client.get("/labels").json()["labels"]} == {"synthetic"}


def test_synth_is_deterministic_and_noisy(tmp_path):
    a = synth.generate(tmp_path / "a", 3, seed=1)
    b = synth.generate(tmp_path / "b", 3, seed=1)
    assert a == b
    assert (tmp_path / "a" / a[0][0]).read_text() == (tmp_path / "b" / b[0][0]).read_text()


def test_training_refused_without_classes_or_enough_docs(client):
    r = client.post("/train")
    assert r.status_code == 422 and r.json()["error"]["code"] == "NOT_ENOUGH_CLASSES"
    a = client.post("/categories", json={"name": "A"}).json()["id"]
    b = client.post("/categories", json={"name": "B"}).json()["id"]
    client.post("/labels", json={"rel_path": "garage.txt", "category_id": a})
    client.post("/labels", json={"rel_path": "notes.md", "category_id": b})
    r = client.post("/train")
    assert (
        r.status_code == 422
        and r.json()["error"]["code"] == "NOT_ENOUGH_DOCS"
        and "A: 1" in r.json()["error"]["message"]
    )


def test_bad_params(client):
    client.post("/datasets/synthetic", json={"per_class": 8})
    assert client.post("/train", json={"algos": ["nope"]}).json()["error"]["code"] == "BAD_ALGO"
    assert client.post("/train", json={"test_size": 0.9}).json()["error"]["code"] == "BAD_TEST_SIZE"


def test_multi_algo_training_selects_best(trained):
    client, run_id = trained
    run = client.get(f"/train/{run_id}").json()
    assert run["status"] == "done" and run["n_train"] + run["n_test"] == 60
    assert {m["algo"] for m in run["models"]} == {"logreg", "svm", "nb"}
    assert all(
        m["accuracy"] >= 0.8 for m in run["models"]
    )  # synthetic data is easy; a failure here means a pipeline bug
    best = max(run["models"], key=lambda m: m["macro_f1"])
    assert run["best_model_name"] == best["algo"] or best["macro_f1"] == max(m["macro_f1"] for m in run["models"])
    assert sum(m["is_active"] for m in run["models"]) == 1
    active = [m for m in run["models"] if m["is_active"]][0]
    assert active["macro_f1"] == best["macro_f1"]
    assert all(m["cv_mean"] is not None for m in run["models"])


def test_metrics_endpoint(trained):
    client, run_id = trained
    mid = client.get(f"/train/{run_id}").json()["models"][0]["id"]
    m = client.get(f"/models/{mid}/metrics").json()
    met = m["metrics"]
    assert set(met["confusion"]["labels"]) == {"Contract", "Invoice", "Other", "Report", "Resume"}
    assert len(met["confusion"]["matrix"]) == 5
    assert {"precision", "recall", "f1", "support"} <= set(met["per_class"][0])
    assert met["meta"]["sklearn"] and "overfit" in met and met["cv_folds"] >= 2
    assert all(len(v) == 10 for v in m["top_features"].values())
    assert client.get("/models/999/metrics").status_code == 404


def test_top_features_make_sense(trained):
    client, run_id = trained
    mid = [m for m in client.get(f"/train/{run_id}").json()["models"] if m["algo"] == "logreg"][0]["id"]
    feats = client.get(f"/models/{mid}/metrics").json()["top_features"]
    inv = {f["word"] for f in feats["Invoice"]}
    assert inv & {"moneytoken", "invoice", "bill", "total", "tax", "subtotal", "bill to", "total due", "due"}
    res = {f["word"] for f in feats["Resume"]}
    assert res & {"resume", "skills", "objective", "education", "work experience", "references", "experience"}


def test_predict_single_and_folder(trained, docs):
    client, _ = trained
    r = client.post("/predict", json={"rel_path": "_synthetic/invoice/invoice_001.txt"}).json()
    assert r["predictions"][0]["category"] == "Invoice" and len(r["predictions"]) == 3
    assert sum(p["confidence"] for p in r["predictions"]) <= 1.0001 and r["top_words"]
    assert r["uncertain"] is False
    job = client.post("/predict-folder", json={"path": "_synthetic/resume"}).json()
    assert job["total"] == 12
    client.app.state.container.folder_jobs[job["job_id"]]["thread"].join()
    st = client.get(f"/predict-folder/{job['job_id']}").json()
    assert st["state"] == "done" and len(st["results"]) == 12
    assert sum(x["predictions"][0]["category"] == "Resume" for x in st["results"]) >= 10
    assert client.get("/predictions").json()["predictions"]


def test_predict_errors_and_uncertain(trained, docs):
    client, _ = trained
    assert client.post("/predict", json={"rel_path": "../../etc/passwd"}).status_code == 400
    assert client.post("/predict", json={"rel_path": "nope.txt"}).status_code == 404
    (docs / "blank.txt").write_text("   ")
    assert client.post("/predict", json={"rel_path": "blank.txt"}).json()["error"]["code"] == "NO_TEXT"
    client.app.state.container.settings.uncertain_below = 0.9999
    assert client.post("/predict", json={"rel_path": "garage.txt"}).json()["uncertain"] is True


def test_predict_without_model(client):
    assert client.post("/predict", json={"rel_path": "garage.txt"}).json()["error"]["code"] == "NO_ACTIVE_MODEL"
    assert client.post("/predict-folder").status_code == 409


def test_feedback_retrain_and_rollback(trained):
    client, run_id = trained
    first_active = client.app.state.container.registry.active()
    cats = {c["name"]: c["id"] for c in client.get("/categories").json()["categories"]}
    r = client.post("/feedback", json={"rel_path": "garage.txt", "correct_category_id": cats["Other"]})
    assert r.status_code == 201 and r.json()["source"] == "feedback"
    run2 = client.app.state.container.trainer.run_blocking(["logreg"])
    m2 = client.get(f"/train/{run2}").json()["models"][0]
    assert m2["version"] == 4 and m2["is_active"]  # versions keep incrementing across runs
    assert client.post(f"/models/{first_active['id']}/activate").status_code == 200  # rollback
    assert client.app.state.container.registry.active()["id"] == first_active["id"]
    assert sum(m["is_active"] for m in client.get("/models").json()["models"]) == 1
    assert client.post("/models/999/activate").status_code == 404


def test_duplicate_texts_dropped_to_avoid_leakage(client, docs):
    client.post("/datasets/synthetic", json={"per_class": 8})
    cid = client.get("/categories").json()["categories"][0]["id"]
    (docs / "dup1.txt").write_text("exactly the same text", encoding="utf-8")
    (docs / "dup2.txt").write_text("exactly the same text", encoding="utf-8")
    client.post("/labels", json={"rel_path": "dup1.txt", "category_id": cid})
    client.post("/labels", json={"rel_path": "dup2.txt", "category_id": cid})
    run_id = client.app.state.container.trainer.run_blocking(["nb"])
    assert client.get(f"/train/{run_id}").json()["params"]["duplicates_dropped"] >= 1


def test_missing_label_files_reported(client, docs):
    client.post("/datasets/synthetic", json={"per_class": 8})
    (docs / "_synthetic" / "invoice" / "invoice_001.txt").unlink()
    run_id = client.app.state.container.trainer.run_blocking(["nb"])
    assert "_synthetic/invoice/invoice_001.txt" in client.get(f"/train/{run_id}").json()["params"]["missing_files"]


def test_overfit_flag_for_memorising_tiny_dataset(client):
    from app.ml.evaluator import evaluate
    from app.ml.pipeline import build_pipeline

    X = [f"apple {i} common" for i in range(4)] + [f"banana {i} common" for i in range(4)]
    y = ["a"] * 4 + ["b"] * 4
    pipe = build_pipeline("logreg", 1000, (1, 1), 1).fit(X, y)
    # test set deliberately contradicts the training pattern -> big train/test gap
    m = evaluate(pipe, X, y, ["apple common", "banana common"], ["b", "a"])
    assert m["train_accuracy"] == 1.0 and m["accuracy"] == 0.0 and m["overfit"] is True


def test_model_card_markdown(trained):
    client, run_id = trained
    mid = client.get(f"/train/{run_id}").json()["models"][0]["id"]
    r = client.get(f"/models/{mid}/card")
    assert (
        r.status_code == 200 and r.text.startswith("# Model card") and "| Invoice |" in r.text and "Macro F1" in r.text
    )
