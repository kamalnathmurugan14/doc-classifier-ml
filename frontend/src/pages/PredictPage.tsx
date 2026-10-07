import { useState } from "react";
import { api, post, type Category, type Entry, type FolderJob, type Prediction } from "../api/client";
import { FileExplorer } from "../components/FileExplorer";
import { LabelDropdown } from "../components/LabelDropdown";
import { PredictionBars } from "../components/PredictionBars";
import { useAsync } from "../hooks/useAsync";

export function PredictPage() {
  const cats = useAsync(() => api<{ categories: Category[] }>("/categories"), []);
  const [pred, setPred] = useState<Prediction | null>(null);
  const [folder, setFolder] = useState<FolderJob | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [fixing, setFixing] = useState(false);
  const [fix, setFix] = useState<number | null>(null);
  const [note, setNote] = useState<string | null>(null);

  const guard = async (fn: () => Promise<void>) => {
    setError(null);
    setNote(null);
    try {
      await fn();
    } catch (e) {
      setError((e as Error).message);
    }
  };
  const predictFile = (e: Entry) =>
    guard(async () => {
      setFolder(null);
      setFixing(false);
      setPred(await post<Prediction>("/predict", { rel_path: e.path }));
    });
  const predictFolder = () =>
    guard(async () => {
      setPred(null);
      const { job_id } = await post<{ job_id: string }>("/predict-folder", {});
      for (;;) {
        const j = await api<FolderJob>(`/predict-folder/${job_id}`);
        setFolder(j);
        if (j.state === "done") break;
        await new Promise((r) => setTimeout(r, 400));
      }
    });
  const sendFeedback = () =>
    guard(async () => {
      if (!pred || fix == null) return;
      await post("/feedback", { rel_path: pred.rel_path, correct_category_id: fix });
      setNote("Thanks! Saved as a new label. Retrain on the Train page to learn from it.");
      setFixing(false);
    });

  return (
    <>
      <h2>Predict</h2>
      <p className="muted">Click a file to classify it, or classify everything in your documents folder.</p>
      <div className="row" style={{ marginBottom: 10 }}>
        <button type="button" onClick={predictFolder}>
          Classify whole folder
        </button>
      </div>
      {error && (
        <p className="error" role="alert">
          {error}
        </p>
      )}
      <div className="two">
        <FileExplorer onOpenFile={predictFile} />
        <div>
          {pred && (
            <div className="card">
              <PredictionBars p={pred} />
              {!fixing && (
                <button
                  type="button"
                  onClick={() => {
                    setFixing(true);
                    setFix(null);
                  }}
                >
                  Wrong? Correct it
                </button>
              )}
              {fixing && (
                <div className="row">
                  <LabelDropdown
                    categories={cats.data?.categories ?? []}
                    value={fix}
                    onChange={setFix}
                    label="Correct category"
                  />
                  <button className="primary" type="button" disabled={fix == null} onClick={sendFeedback}>
                    Submit
                  </button>
                </div>
              )}
              {note && <p role="status">{note}</p>}
            </div>
          )}
          {folder && (
            <div className="card">
              <h3 style={{ marginTop: 0 }}>
                Folder results {folder.state === "running" && `(${folder.done}/${folder.total})`}
              </h3>
              <table>
                <thead>
                  <tr>
                    <th>file</th>
                    <th>prediction</th>
                    <th className="num">confidence</th>
                  </tr>
                </thead>
                <tbody>
                  {folder.results.map((r) => (
                    <tr key={r.rel_path}>
                      <td>{r.rel_path}</td>
                      <td>
                        {r.uncertain ? (
                          <span className="chip warnchip">Uncertain</span>
                        ) : (
                          r.predictions[0].category
                        )}
                      </td>
                      <td className="num">{(r.predictions[0].confidence * 100).toFixed(0)}%</td>
                    </tr>
                  ))}
                </tbody>
              </table>
              {folder.errors.map((e) => (
                <p key={e.rel_path} className="error">
                  {e.rel_path}: {e.error}
                </p>
              ))}
            </div>
          )}
          {!pred && !folder && <p className="empty">No predictions yet.</p>}
        </div>
      </div>
    </>
  );
}
