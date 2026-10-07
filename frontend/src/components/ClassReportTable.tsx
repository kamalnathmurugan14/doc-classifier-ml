import type { ClassRow } from "../api/client";

export function ClassReportTable({ rows }: { rows: ClassRow[] }) {
  return (
    <table>
      <thead>
        <tr>
          <th>class</th>
          <th className="num">precision</th>
          <th className="num">recall</th>
          <th className="num">F1</th>
          <th className="num">support</th>
        </tr>
      </thead>
      <tbody>
        {rows.map((r) => (
          <tr key={r.class}>
            <td>{r.class}</td>
            <td className="num">{r.precision.toFixed(2)}</td>
            <td className="num">{r.recall.toFixed(2)}</td>
            <td className="num">{r.f1.toFixed(2)}</td>
            <td className="num">{r.support}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}
