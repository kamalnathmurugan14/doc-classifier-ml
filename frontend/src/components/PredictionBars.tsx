import type { Prediction } from "../api/client";

/** Top-3 confidence bars. Below the threshold the top answer is shown as "Uncertain". */
export function PredictionBars({ p }: { p: Prediction }) {
  return (
    <div>
      <h3 style={{ marginTop: 0 }}>
        {p.uncertain ? <span className="chip warnchip">Uncertain</span> : p.predictions[0].category}{" "}
        <span className="muted">{p.rel_path}</span>
      </h3>
      {p.predictions.map((x) => (
        <div className="bar wide" key={x.category}>
          <span>{x.category}</span>
          <div
            className="track"
            role="meter"
            aria-label={`${x.category} confidence`}
            aria-valuemin={0}
            aria-valuemax={100}
            aria-valuenow={Math.round(x.confidence * 100)}
          >
            <div
              className="fill"
              style={{
                width: `${x.confidence * 100}%`,
                background: p.uncertain ? "var(--bar-kw)" : "var(--bar-hyb)",
              }}
            />
          </div>
          <span className="num">{(x.confidence * 100).toFixed(1)}%</span>
        </div>
      ))}
      {p.top_words.length > 0 && (
        <p className="muted">
          Words that pushed towards “{p.predictions[0].category}”: {p.top_words.map((w) => w.word).join(", ")}
        </p>
      )}
    </div>
  );
}
