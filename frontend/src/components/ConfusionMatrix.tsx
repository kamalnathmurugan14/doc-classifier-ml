/** Heatmap: rows = true class, columns = predicted class. Diagonal = correct. */
export function ConfusionMatrix({ labels, matrix }: { labels: string[]; matrix: number[][] }) {
  const max = Math.max(1, ...matrix.flat());
  return (
    <div style={{ overflowX: "auto" }}>
      <table className="confusion" aria-label="Confusion matrix">
        <thead>
          <tr>
            <th scope="col">true ↓ / predicted →</th>
            {labels.map((l) => (
              <th key={l} scope="col" className="num">
                {l}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {matrix.map((row, i) => (
            <tr key={labels[i]}>
              <th scope="row">{labels[i]}</th>
              {row.map((v, j) => (
                <td
                  key={j}
                  className="num"
                  title={`${v} × true ${labels[i]} predicted as ${labels[j]}`}
                  style={{
                    background: `color-mix(in srgb, ${i === j ? "var(--ok)" : "var(--danger)"} ${Math.round((v / max) * 70)}%, transparent)`,
                    fontWeight: i === j ? 700 : 400,
                  }}
                >
                  {v}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
