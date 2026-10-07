import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";
import type { Metrics, ModelRow, Prediction } from "../api/client";
import { ConfusionMatrix } from "./ConfusionMatrix";
import { MetricsCards } from "./MetricsCards";
import { ModelVersionList } from "./ModelVersionList";
import { PredictionBars } from "./PredictionBars";
import { TopFeaturesChart } from "./TopFeaturesChart";

afterEach(() => vi.restoreAllMocks());

const metrics = (overfit: boolean): Metrics => ({
  id: 1,
  algo: "logreg",
  version: 1,
  is_active: true,
  accuracy: 0.9,
  macro_f1: 0.88,
  metrics: {
    weighted_f1: 0.89,
    train_accuracy: 1,
    overfit,
    per_class: [],
    confusion: {
      labels: ["A", "B"],
      matrix: [
        [5, 1],
        [0, 4],
      ],
    },
    cv_folds: 5,
    cv_mean: 0.85,
    cv_std: 0.02,
    train_seconds: 0.1,
    algo_label: "LR",
    meta: { sklearn: "1.5", python: "3.11" },
  },
  top_features: {
    A: [
      { word: "alpha", weight: 2 },
      { word: "beta", weight: 1 },
    ],
    B: [{ word: "gamma", weight: 3 }],
  },
});

describe("MetricsCards", () => {
  it("shows percentages and CV", () => {
    render(<MetricsCards m={metrics(false)} />);
    expect(screen.getByText("90.0%")).toBeInTheDocument();
    expect(screen.getByText(/85.0% ± 2.0%/)).toBeInTheDocument();
    expect(screen.queryByRole("alert")).toBeNull();
  });
  it("warns about overfitting", () => {
    render(<MetricsCards m={metrics(true)} />);
    expect(screen.getByRole("alert")).toHaveTextContent(/overfitting/i);
  });
});

describe("ConfusionMatrix", () => {
  it("renders every cell with headers", () => {
    render(
      <ConfusionMatrix
        labels={["A", "B"]}
        matrix={[
          [5, 1],
          [0, 4],
        ]}
      />,
    );
    expect(screen.getByRole("table", { name: "Confusion matrix" })).toBeInTheDocument();
    expect(screen.getByText("5")).toBeInTheDocument();
    expect(screen.getAllByRole("columnheader")).toHaveLength(3);
  });
});

describe("TopFeaturesChart", () => {
  it("switches class tabs", async () => {
    render(<TopFeaturesChart features={metrics(false).top_features} />);
    expect(screen.getByText("alpha")).toBeInTheDocument();
    await userEvent.click(screen.getByRole("tab", { name: "B" }));
    expect(screen.getByText("gamma")).toBeInTheDocument();
    expect(screen.queryByText("alpha")).toBeNull();
  });
});

describe("PredictionBars", () => {
  const base: Prediction = {
    rel_path: "x.txt",
    uncertain: false,
    model_id: 1,
    top_words: [{ word: "invoice", contribution: 1 }],
    predictions: [
      { category: "Invoice", confidence: 0.8 },
      { category: "Other", confidence: 0.2 },
    ],
  };
  it("shows the top category and word hints", () => {
    render(<PredictionBars p={base} />);
    expect(screen.getByRole("heading")).toHaveTextContent("Invoice");
    expect(screen.getAllByRole("meter")).toHaveLength(2);
    expect(screen.getByText(/invoice/i, { selector: "p" })).toBeInTheDocument();
  });
  it("shows Uncertain for low confidence", () => {
    render(<PredictionBars p={{ ...base, uncertain: true }} />);
    expect(screen.getByText("Uncertain")).toBeInTheDocument();
  });
});

describe("ModelVersionList", () => {
  const rows: ModelRow[] = [
    {
      id: 2,
      algo: "svm",
      version: 2,
      accuracy: 0.9,
      macro_f1: 0.9,
      is_active: true,
      created_at: "2026-01-01T00:00:00Z",
    },
    {
      id: 1,
      algo: "nb",
      version: 1,
      accuracy: 0.8,
      macro_f1: 0.7,
      is_active: false,
      created_at: "2026-01-01T00:00:00Z",
    },
  ];
  it("lets you roll back to an older version", async () => {
    const onActivate = vi.fn();
    render(<ModelVersionList models={rows} onActivate={onActivate} />);
    expect(screen.getByRole("button", { name: "Active" })).toBeDisabled();
    await userEvent.click(screen.getByRole("button", { name: /roll back/i }));
    expect(onActivate).toHaveBeenCalledWith(1);
  });
  it("has an empty state", () => {
    render(<ModelVersionList models={[]} onActivate={() => {}} />);
    expect(screen.getByText(/no models yet/i)).toBeInTheDocument();
  });
});
