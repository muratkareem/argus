import {
  cleanup,
  fireEvent,
  render,
  screen,
  within,
} from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import Laboratory from "./Laboratory";
import { api } from "../api";
import type { BenchmarkCatalog, Experiment, Models } from "../types";

vi.mock("../api", async (original) => ({
  ...(await original<typeof import("../api")>()),
  api: vi.fn(),
}));
afterEach(cleanup);
const emptyWorkspace: Models = { active_version: null, experiments: [] };
const catalog: BenchmarkCatalog = {
  datasets: [
    {
      id: "ulb",
      name: "ULB",
      data_kind: "real",
      status: "evaluated",
      source: "https://www.kaggle.com",
      license: "ODbL",
      blocker: null,
    },
    {
      id: "ieee_cis",
      name: "IEEE-CIS",
      data_kind: "real",
      status: "access_required",
      source: "https://www.kaggle.com",
      license: "Competition rules",
      blocker:
        "Official download returned HTTP 401. Accept rules and use authorized Kaggle access.",
    },
    {
      id: "paysim",
      name: "PaySim",
      data_kind: "synthetic",
      status: "not_evaluated",
      source: "https://www.kaggle.com",
      license: "CC BY-SA 4.0",
      blocker: null,
    },
  ],
  experiments: [],
  report_errors: [],
  interpretation:
    "Independent training, not cross-dataset transfer validation.",
};
beforeEach(() =>
  vi
    .mocked(api)
    .mockImplementation(async (path) =>
      path === "/models" ? emptyWorkspace : catalog,
    ),
);
describe("dataset evidence selection", () => {
  it("allows dataset selection even without a local active model and never invents blocked results", async () => {
    render(<Laboratory revision={0} fail={vi.fn()} />);
    fireEvent.change(await screen.findByLabelText("Dataset"), {
      target: { value: "ieee_cis" },
    });
    expect(
      within(
        screen
          .getByText(/No metrics are claimed/)
          .closest(".empty") as HTMLElement,
      ).getByText(/Official download returned HTTP 401/),
    ).toBeVisible();
    expect(screen.queryByText("Model comparison")).not.toBeInTheDocument();
    expect(screen.getByText(/No metrics are claimed/)).toBeVisible();
    fireEvent.change(screen.getByLabelText("Dataset"), {
      target: { value: "paysim" },
    });
    expect(
      screen.getByText(/Simulation benchmark; not real transaction evidence/),
    ).toBeVisible();
    expect(screen.getByText(/No executed experiments/)).toBeVisible();
  });
  it("compares only supplied reports with test sizes and domain caveats", async () => {
    const fixture: Experiment = {
      version: "test-only",
      provenance: "ulb",
      seed: 42,
      rows: 100,
      fraud_rows: 2,
      duplicates_removed: 0,
      created_at: "2026-01-01T00:00:00Z",
      duration_seconds: 0,
      dataset_id: "ulb",
      data_kind: "real",
      split: "chronological",
      selected_model: "Fixture model",
      partitions: { test: { rows: 100, fraud: 2 } },
      models: [
        {
          name: "Fixture model",
          threshold: 0.5,
          validation_average_precision: 0.1,
          feature_importance: [],
          test: {
            precision: 0.5,
            recall: 0.5,
            f1: 0.5,
            average_precision: 0.1234,
            roc_auc: 0.5,
            false_positive_rate: 1 / 98,
            confusion_matrix: [
              [97, 1],
              [1, 1],
            ],
            pr_curve: [],
          },
        },
      ],
    };
    vi.mocked(api).mockImplementation(async (path) =>
      path === "/models"
        ? emptyWorkspace
        : { ...catalog, experiments: [fixture] },
    );
    render(<Laboratory revision={0} fail={vi.fn()} />);
    fireEvent.click(await screen.findByText("Verified dataset comparison"));
    const table = screen.getByRole("table");
    expect(within(table).getByText("0.1234")).toBeVisible();
    expect(within(table).getByText("100 / 2")).toBeVisible();
    expect(within(table).getByText("100 rows · seed 42")).toBeVisible();
    expect(
      screen.getByText(/not cross-dataset transfer validation/),
    ).toBeVisible();
  });
});
