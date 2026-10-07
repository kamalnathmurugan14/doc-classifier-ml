import type { ModelRow } from "../api/client";

interface Props {
  models: ModelRow[];
  onActivate: (id: number) => void;
  onSelect?: (id: number) => void;
}

export function ModelVersionList({ models, onActivate, onSelect }: Props) {
  if (models.length === 0) return <p className="empty">No models yet. Train one first.</p>;
  return (
    <table>
      <thead>
        <tr>
          <th>version</th>
          <th>algorithm</th>
          <th className="num">accuracy</th>
          <th className="num">macro-F1</th>
          <th>created</th>
          <th />
        </tr>
      </thead>
      <tbody>
        {models.map((m) => (
          <tr key={m.id}>
            <td>
              v{m.version} {m.is_active && <span className="chip active">active</span>}
            </td>
            <td>{m.algo}</td>
            <td className="num">{(m.accuracy * 100).toFixed(1)}%</td>
            <td className="num">{(m.macro_f1 * 100).toFixed(1)}%</td>
            <td className="muted">{new Date(m.created_at).toLocaleString()}</td>
            <td className="row">
              {onSelect && (
                <button type="button" onClick={() => onSelect(m.id)}>
                  Metrics
                </button>
              )}
              <button type="button" disabled={m.is_active} onClick={() => onActivate(m.id)}>
                {m.is_active ? "Active" : "Activate / roll back"}
              </button>
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}
