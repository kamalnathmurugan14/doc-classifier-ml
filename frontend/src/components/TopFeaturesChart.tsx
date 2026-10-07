import { useState } from "react";

export function TopFeaturesChart({
  features,
}: {
  features: Record<string, { word: string; weight: number }[]>;
}) {
  const classes = Object.keys(features);
  const [cls, setCls] = useState(classes[0]);
  const rows = features[cls] ?? [];
  const max = Math.max(...rows.map((r) => r.weight), 1e-9);
  return (
    <div>
      <div className="row" role="tablist" aria-label="Class">
        {classes.map((c) => (
          <button
            key={c}
            type="button"
            role="tab"
            aria-selected={c === cls}
            className={`chip${c === cls ? " active" : ""}`}
            onClick={() => setCls(c)}
          >
            {c}
          </button>
        ))}
      </div>
      {rows.map((r) => (
        <div className="bar wide" key={r.word}>
          <span>{r.word}</span>
          <div className="track">
            <div
              className="fill"
              style={{ width: `${(Math.max(r.weight, 0) / max) * 100}%`, background: "var(--accent)" }}
            />
          </div>
          <span className="num">{r.weight.toFixed(2)}</span>
        </div>
      ))}
    </div>
  );
}
