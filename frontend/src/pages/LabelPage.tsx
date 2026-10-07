import { useCallback, useEffect, useState, type FormEvent } from "react";
import { api, post, qs, type Category, type Entry, type LabelRow } from "../api/client";
import { FileExplorer } from "../components/FileExplorer";
import { LabelDropdown } from "../components/LabelDropdown";
import { useAsync } from "../hooks/useAsync";

export function LabelPage() {
  const cats = useAsync(() => api<{ categories: Category[]; min_docs_per_class: number }>("/categories"), []);
  const labels = useAsync(() => api<{ labels: LabelRow[] }>("/labels"), []);
  const [file, setFile] = useState<Entry | null>(null);
  const [preview, setPreview] = useState<string>("");
  const [choice, setChoice] = useState<number | null>(null);
  const [newName, setNewName] = useState("");
  const [msg, setMsg] = useState<{ kind: "ok" | "err"; text: string } | null>(null);
  const [version, setVersion] = useState(0);

  const current = file ? labels.data?.labels.find((l) => l.rel_path === file.path) : undefined;
  useEffect(() => setChoice(current?.category_id ?? null), [current?.category_id, file?.path]);
  useEffect(() => {
    if (!file) return;
    setPreview("Loading preview…");
    api<{ text: string; truncated: boolean }>("/fs/preview?" + qs({ path: file.path }))
      .then((r) => setPreview(r.text + (r.truncated ? "\n…" : "")))
      .catch((e: Error) => setPreview("⚠ " + e.message));
  }, [file]);

  const refresh = useCallback(() => {
    cats.reload();
    labels.reload();
    setVersion((v) => v + 1);
  }, [cats, labels]);
  const run = async (fn: () => Promise<unknown>, ok: string) => {
    try {
      await fn();
      setMsg({ kind: "ok", text: ok });
      refresh();
    } catch (e) {
      setMsg({ kind: "err", text: (e as Error).message });
    }
  };
  const addCategory = (e: FormEvent) => {
    e.preventDefault();
    if (newName.trim())
      void run(() => post("/categories", { name: newName.trim() }), `Added ${newName.trim()}`).then(() =>
        setNewName(""),
      );
  };

  return (
    <>
      <h2>Label documents</h2>
      <div className="two">
        <div>
          <FileExplorer key={version} onOpenFile={setFile} />
          <div className="card">
            <h3 style={{ marginTop: 0 }}>Categories</h3>
            {cats.error && (
              <p className="error" role="alert">
                {cats.error}
              </p>
            )}
            {cats.data?.categories.length === 0 && (
              <p className="empty">No categories yet — add one below or generate a sample dataset.</p>
            )}
            <div className="row">
              {cats.data?.categories.map((c) => (
                <span
                  key={c.id}
                  className="chip"
                  style={{ borderColor: c.color }}
                  title={
                    c.needs_more ? `needs at least ${cats.data?.min_docs_per_class} labels` : "enough labels"
                  }
                >
                  {c.name}: {c.count} {c.needs_more && "⚠ needs more labels"}
                </span>
              ))}
            </div>
            <form className="row" onSubmit={addCategory} style={{ marginTop: 10 }}>
              <label className="sr-only" htmlFor="newcat">
                New category
              </label>
              <input
                id="newcat"
                type="text"
                placeholder="New category (e.g. Invoice)"
                value={newName}
                onChange={(e) => setNewName(e.target.value)}
              />
              <button type="submit">Add</button>
              <button
                type="button"
                onClick={() =>
                  run(
                    () => post("/datasets/synthetic", { per_class: 20 }),
                    "Generated 100 synthetic labelled documents",
                  )
                }
              >
                Generate synthetic dataset
              </button>
            </form>
          </div>
        </div>
        <div className="card">
          <h3 style={{ marginTop: 0 }}>{file ? file.path : "Select a file"}</h3>
          {!file && <p className="empty">Click a file in the explorer to preview and label it.</p>}
          {file && (
            <>
              <pre className="preview" tabIndex={0} aria-label="Document preview">
                {preview}
              </pre>
              <div className="row">
                <LabelDropdown categories={cats.data?.categories ?? []} value={choice} onChange={setChoice} />
                <button
                  className="primary"
                  type="button"
                  disabled={choice == null}
                  onClick={() =>
                    run(() => post("/labels", { rel_path: file.path, category_id: choice }), "Label saved")
                  }
                >
                  Save label
                </button>
                {current && (
                  <button
                    type="button"
                    onClick={() =>
                      run(() => api(`/labels/${current.id}`, { method: "DELETE" }), "Label removed")
                    }
                  >
                    Remove
                  </button>
                )}
              </div>
              {current && (
                <p className="muted">
                  Current label: <strong>{current.category}</strong> ({current.source})
                </p>
              )}
            </>
          )}
          {msg && (
            <p role="status" className={msg.kind === "err" ? "error" : ""}>
              {msg.text}
            </p>
          )}
        </div>
      </div>
    </>
  );
}
