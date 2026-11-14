import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";
import { ModelDiagnostics } from "./ModelDiagnostics";
import type { Model } from "../types";
afterEach(cleanup);
const model = {
  name: "Logistic Regression",
  threshold: 0.5,
  test: { false_negative_rate: 0.25, brier_score: 0.12 },
  validation_threshold_analysis: {
    partition: "validation",
    cost_assumptions: {
      unit: "arbitrary units",
      false_positive: 1,
      false_negative: 25,
    },
    points: [
      {
        threshold: 0.5,
        precision: 0.6,
        recall: 0.75,
        f1: 0.667,
        false_positives: 2,
        false_negatives: 1,
        estimated_cost: 27,
      },
      {
        threshold: 0.9,
        precision: 1,
        recall: 0.25,
        f1: 0.4,
        false_positives: 0,
        false_negatives: 3,
        estimated_cost: 75,
      },
    ],
  },
} as Model;
describe("measured model diagnostics", () => {
  it("shows measured validation threshold trade-offs with explicit cost assumptions", () => {
    render(<ModelDiagnostics model={model} />);
    expect(screen.getByText("27")).toBeVisible();
    expect(
      screen.getByText(/illustrative costs are not measured financial losses/),
    ).toBeVisible();
    fireEvent.change(screen.getByLabelText("Validation threshold"), {
      target: { value: "0.9" },
    });
    expect(screen.getByText("75")).toBeVisible();
    expect(screen.getByText("0.4000")).toBeVisible();
    expect(model.test.false_negative_rate).toBe(0.25);
  });
  it("honestly labels unavailable measurements in historical experiments", () => {
    render(
      <ModelDiagnostics
        model={{ name: "Legacy", threshold: 0.5, test: {} } as Model}
      />,
    );
    expect(screen.getByText(/ROC curve was not recorded/)).toBeVisible();
    expect(
      screen.getByText(/Validation threshold analysis was not recorded/),
    ).toBeVisible();
    expect(screen.getAllByText("Not recorded")).toHaveLength(3);
  });
});
