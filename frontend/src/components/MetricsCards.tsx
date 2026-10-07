import type { Metrics } from "../api/client";

const pct = (x: number | null | undefined) => (x == null ? "–" : (x * 100).toFixed(1) + "%");

export function MetricsCards({ m }: { m: Metrics }) {
  const x = m.metrics;
  const cards = [
    ["Accuracy (test)", pct(m.accuracy)],
    ["Macro F1", pct(m.macro_f1)],
    ["Weighted F1", pct(x.weighted_f1)],
    ["Train accuracy", pct(x.train_accuracy)],
    [`CV macro-F1 (${x.cv_folds}-fold)`, x.cv_mean == null ? "–" : `${pct(x.cv_mean)} ± ${pct(x.cv_std)}`],
  ];
  return (
    <>
      <div className="cards">
        {cards.map(([k, v]) => (
          <div className="card stat" key={k}>
            <div className="muted">{k}</div>
            <div className="big">{v}</div>
          </div>
        ))}
      </div>
      {x.overfit && (
        <p className="warn" role="alert">
          ⚠ Possible overfitting: train accuracy is much higher than test accuracy. Label more documents or
          simplify the model.
        </p>
      )}
    </>
  );
}
