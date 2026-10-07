// Tiny typed fetch wrapper. Every backend error has the shape { error: { code, message } }.
export const API_URL: string = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

export class ApiError extends Error {
  constructor(
    public code: string,
    message: string,
    public status: number,
  ) {
    super(message);
  }
}

export async function api<T>(path: string, init?: RequestInit): Promise<T> {
  let res: Response;
  try {
    res = await fetch(`${API_URL}${path}`, init);
  } catch {
    throw new ApiError("NETWORK", "Cannot reach the backend. Is it running on " + API_URL + "?", 0);
  }
  if (res.status === 204) return undefined as T;
  const body = await res.json().catch(() => ({}));
  if (!res.ok) {
    throw new ApiError(
      body?.error?.code ?? "HTTP_" + res.status,
      body?.error?.message ?? res.statusText,
      res.status,
    );
  }
  return body as T;
}

export const post = <T>(path: string, body?: unknown) =>
  api<T>(path, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body ?? {}),
  });

export const qs = (params: Record<string, string | number | undefined>) =>
  new URLSearchParams(
    Object.entries(params)
      .filter(([, v]) => v !== undefined && v !== "")
      .map(([k, v]) => [k, String(v)]),
  ).toString();

// ---- types -------------------------------------------------------------
export interface Entry {
  name: string;
  type: "dir" | "file";
  size: number;
  modified: string;
  path: string;
}
export interface Tree {
  path: string;
  entries: Entry[];
}
export interface Category {
  id: number;
  name: string;
  color: string;
  count: number;
  needs_more: boolean;
}
export interface LabelRow {
  id: number;
  rel_path: string;
  source: string;
  category_id: number;
  category: string;
}
export interface TrainModel {
  id: number;
  algo: string;
  label: string;
  version: number;
  accuracy: number;
  macro_f1: number;
  is_active: boolean;
  cv_mean: number | null;
  cv_std: number | null;
  train_seconds: number;
  overfit: boolean;
}
export interface TrainRun {
  id: number;
  status: "running" | "done" | "failed";
  progress: string;
  n_train: number | null;
  n_test: number | null;
  best_model_name: string | null;
  error: string | null;
  models: TrainModel[];
  params: { missing_files: string[]; duplicates_dropped: number; class_counts: Record<string, number> };
}
export interface ClassRow {
  class: string;
  precision: number;
  recall: number;
  f1: number;
  support: number;
}
export interface Metrics {
  id: number;
  algo: string;
  version: number;
  is_active: boolean;
  accuracy: number;
  macro_f1: number;
  metrics: {
    weighted_f1: number;
    train_accuracy: number;
    overfit: boolean;
    per_class: ClassRow[];
    confusion: { labels: string[]; matrix: number[][] };
    cv_folds: number;
    cv_mean: number | null;
    cv_std: number | null;
    train_seconds: number;
    algo_label: string;
    meta: { sklearn: string; python: string };
  };
  top_features: Record<string, { word: string; weight: number }[]>;
}
export interface ModelRow {
  id: number;
  algo: string;
  version: number;
  accuracy: number;
  macro_f1: number;
  is_active: boolean;
  created_at: string;
}
export interface Prediction {
  rel_path: string;
  predictions: { category: string; confidence: number }[];
  uncertain: boolean;
  top_words: { word: string; contribution: number }[];
  model_id: number;
}
export interface FolderJob {
  state: "running" | "done";
  done: number;
  total: number;
  results: Prediction[];
  errors: { rel_path: string; error: string }[];
}
