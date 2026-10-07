import { useState } from "react";
import { Link } from "react-router-dom";
import type { TrainRun } from "../api/client";
import { TrainPanel } from "../components/TrainPanel";

export function TrainPage() {
  const [run, setRun] = useState<TrainRun | null>(null);
  return (
    <>
      <h2>Train</h2>
      <p className="muted">
        Trains each algorithm on a stratified train split, scores it on held-out test data and 5-fold
        cross-validation, then activates the best macro-F1.
      </p>
      <TrainPanel onDone={setRun} />
      {run && (
        <div className="card">
          <h3 style={{ marginTop: 0 }}>Comparison — run #{run.id}</h3>
          <p className="muted">
            {run.n_train} train / {run.n_test} test documents
            {run.params.duplicates_dropped > 0 &&
              ` · ${run.params.duplicates_dropped} exact duplicate(s) dropped to avoid leakage`}
            {run.params.missing_files.length > 0 &&
              ` · ${run.params.missing_files.length} label(s) skipped (file missing/empty)`}
          </p>
          <table>
            <thead>
              <tr>
                <th>algorithm</th>
                <th className="num">accuracy</th>
                <th className="num">macro-F1</th>
                <th className="num">CV macro-F1</th>
                <th className="num">time</th>
                <th />
              </tr>
            </thead>
            <tbody>
              {run.models.map((m) => (
                <tr key={m.id}>
                  <td>
                    {m.label} {m.is_active && <span className="chip active">best</span>}{" "}
                    {m.overfit && <span className="chip warnchip">overfit?</span>}
                  </td>
                  <td className="num">{(m.accuracy * 100).toFixed(1)}%</td>
                  <td className="num">{(m.macro_f1 * 100).toFixed(1)}%</td>
                  <td className="num">
                    {m.cv_mean == null
                      ? "–"
                      : `${(m.cv_mean * 100).toFixed(1)}% ± ${((m.cv_std ?? 0) * 100).toFixed(1)}`}
                  </td>
                  <td className="num">{m.train_seconds}s</td>
                  <td>
                    <Link to={`/metrics?model=${m.id}`}>details</Link>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </>
  );
}
