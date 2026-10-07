import { useState } from "react";
import { api, post, type ModelRow } from "../api/client";
import { ModelVersionList } from "../components/ModelVersionList";
import { useAsync } from "../hooks/useAsync";
import { useNavigate } from "react-router-dom";

export function ModelsPage() {
  const models = useAsync(() => api<{ models: ModelRow[] }>("/models"), []);
  const [error, setError] = useState<string | null>(null);
  const nav = useNavigate();
  const activate = async (id: number) => {
    try {
      await post(`/models/${id}/activate`);
      models.reload();
    } catch (e) {
      setError((e as Error).message);
    }
  };
  return (
    <>
      <h2>Model versions</h2>
      <p className="muted">
        Activate an older version to roll back. Predictions always use the active model.
      </p>
      {models.loading && <p className="muted">Loading…</p>}
      {(models.error || error) && (
        <p className="error" role="alert">
          {models.error ?? error}
        </p>
      )}
      {models.data && (
        <div className="card">
          <ModelVersionList
            models={models.data.models}
            onActivate={activate}
            onSelect={(id) => nav(`/metrics?model=${id}`)}
          />
        </div>
      )}
    </>
  );
}
