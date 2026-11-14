import {
  cleanup,
  fireEvent,
  render,
  screen,
  within,
} from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";
import { ExplanationContributions } from "./ExplanationContributions";
afterEach(cleanup);
describe("explanation hierarchy", () => {
  it("separates positive and negative contributions without inventing meanings", () => {
    const features = [
      { feature: "V1", contribution: 0.7 },
      { feature: "V2", contribution: -0.3 },
      { feature: "Time", contribution: 0.01 },
    ];
    render(
      <ExplanationContributions
        features={features}
        outputSpace="log-odds"
        baseValue={0.2}
        modelVersion="verified"
      />,
    );
    expect(
      within(
        screen.getByRole("region", { name: "Raises the score" }),
      ).getByText("V1"),
    ).toBeVisible();
    expect(
      within(
        screen.getByRole("region", { name: "Lowers the score" }),
      ).getByText("-0.300"),
    ).toBeVisible();
    expect(screen.getByText(/not causal evidence/)).toBeVisible();
    fireEvent.click(screen.getByText("Explanation details and all features"));
    expect(screen.getByText(/SHAP output: log-odds/)).toBeVisible();
    expect(screen.getAllByRole("row")).toHaveLength(4);
    expect(features[0].feature).toBe("V1");
  });
  it("does not fabricate a negative contribution when all are positive", () => {
    render(
      <ExplanationContributions
        features={[{ feature: "V1", contribution: 1 }]}
      />,
    );
    expect(
      within(
        screen.getByRole("region", { name: "Lowers the score" }),
      ).getByText("No contributions in this direction."),
    ).toBeVisible();
  });
});
