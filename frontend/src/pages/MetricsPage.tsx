import { useEffect, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { api, type Metrics, type ModelRow } from "../api/client";
import { ClassReportTable } from "../components/ClassReportTable";
import { ConfusionMatrix } from "../components/ConfusionMatrix";
import { MetricsCards } from "../components/MetricsCards";
import { TopFeaturesChart } from "../components/TopFeaturesChart";
import { useAsync } from "../hooks/useAsync";

export function MetricsPage() {
  const [params, setParams] = useSearchParams();
  const models = useAsync(() => api<{ models: ModelRow[] }>("/models"), []);
  const [id, setId] = useState<number | null>(params.get("model") ? Number(params.get("model")) : null);
  useEffect(() => {
    if (id == null && models.data?.models.length)
      setId((models.data.models.find((m) => m.is_active) ?? models.data.models[0]).id);
  }, [models.data, id]);
  const m = useAsync(
    () => (id == null ? Promise.resolve(null) : api<Metrics>(`/models/${id}/metrics`)),
    [id],
  );

  return (
    <>
      <h2>Metrics</h2>
      {models.error && (
        <p className="error" role="alert">
          {models.error}
        </p>
      )}
      {models.data?.models.length === 0 && (
        <p className="empty">No trained models yet. Go to the Train page.</p>
      )}
      {!!models.data?.models.length && (
        <label className="row" style={{ marginBottom: 12 }}>
          Model
          <select
            value={id ?? ""}
            onChange={(e) => {
              setId(Number(e.target.value));
              setParams({ model: e.target.value });
            }}
          >
            {models.data.models.map((x) => (
              <option key={x.id} value={x.id}>
                v{x.version} · {x.algo}
                {x.is_active ? " (active)" : ""}
              </option>
            ))}
          </select>
        </label>
      )}
      {m.loading && id != null && <p className="muted">Loading…</p>}
      {m.error && (
        <p className="error" role="alert">
          {m.error}
        </p>
      )}
      {m.data && (
        <>
          <MetricsCards m={m.data} />
          <div className="two">
            <div className="card">
              <h3 style={{ marginTop: 0 }}>Confusion matrix</h3>
              <ConfusionMatrix {...m.data.metrics.confusion} />
            </div>
            <div className="card">
              <h3 style={{ marginTop: 0 }}>Per-class report</h3>
              <ClassReportTable rows={m.data.metrics.per_class} />
            </div>
          </div>
          <div className="card">
            <h3 style={{ marginTop: 0 }}>Top words per class</h3>
            <TopFeaturesChart features={m.data.top_features} />
          </div>
          <p className="muted">
            trained with scikit-learn {m.data.metrics.meta.sklearn}, Python {m.data.metrics.meta.python}
          </p>
        </>
      )}
    </>
  );
}
