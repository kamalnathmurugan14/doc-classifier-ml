import { useEffect, useState } from "react";
import { api, post, type TrainRun } from "../api/client";

const ALGOS = [
  ["logreg", "Logistic Regression"],
  ["svm", "Linear SVM (calibrated)"],
  ["nb", "Naive Bayes"],
] as const;

export function TrainPanel({ onDone }: { onDone: (run: TrainRun) => void }) {
  const [algos, setAlgos] = useState<string[]>(ALGOS.map(([k]) => k));
  const [testSize, setTestSize] = useState(0.2);
  const [runId, setRunId] = useState<number | null>(null);
  const [run, setRun] = useState<TrainRun | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (runId == null) return;
    const id = setInterval(async () => {
      try {
        const r = await api<TrainRun>(`/train/${runId}`);
        setRun(r);
        if (r.status !== "running") {
          clearInterval(id);
          setRunId(null);
          if (r.status === "done") onDone(r);
          else setError(r.error);
        }
      } catch (e) {
        setError((e as Error).message);
        clearInterval(id);
        setRunId(null);
      }
    }, 500);
    return () => clearInterval(id);
  }, [runId, onDone]);

  const start = async () => {
    setError(null);
    setRun(null);
    try {
      setRunId((await post<{ run_id: number }>("/train", { algos, test_size: testSize })).run_id);
    } catch (e) {
      setError((e as Error).message);
    }
  };
  const toggle = (k: string) => setAlgos((a) => (a.includes(k) ? a.filter((x) => x !== k) : [...a, k]));
  const running = runId != null;

  return (
    <div className="card">
      <fieldset disabled={running} style={{ border: 0, padding: 0 }}>
        <legend className="muted">Algorithms</legend>
        <div className="row">
          {ALGOS.map(([k, label]) => (
            <label key={k} className="row">
              <input type="checkbox" checked={algos.includes(k)} onChange={() => toggle(k)} /> {label}
            </label>
          ))}
        </div>
        <label className="row" style={{ marginTop: 8 }}>
          Test size
          <input
            type="range"
            min={0.1}
            max={0.5}
            step={0.05}
            value={testSize}
            onChange={(e) => setTestSize(Number(e.target.value))}
            aria-label="Test size"
          />
          <span>{Math.round(testSize * 100)}%</span>
        </label>
      </fieldset>
      <button
        className="primary"
        type="button"
        onClick={start}
        disabled={running || algos.length === 0}
        style={{ marginTop: 8 }}
      >
        {running ? "Training…" : "Train"}
      </button>
      {run && run.status === "running" && <p role="status">{run.progress}</p>}
      {error && (
        <p className="error" role="alert">
          {error}
        </p>
      )}
    </div>
  );
}
