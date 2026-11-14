import {
  fireEvent,
  render,
  screen,
  waitFor,
  cleanup,
} from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { PredictionForm, transactionFeatures } from "./PredictionForm";
import type { Models } from "../types";

const models = {
  active_version: "verified-model",
  experiments: [{ version: "verified-model", provenance: "synthetic" }],
} as Models;
const features = Object.fromEntries(transactionFeatures.map((f, i) => [f, i]));
const prediction = {
  model_version: "verified-model",
  model_name: "Random Forest",
  risk_score: 0.8,
  classification: "flagged",
  risk_category: "high",
  decision_threshold: 0.7,
  metadata: { processing_ms: 1.25, score_type: "uncalibrated" },
};
const respond = (data: unknown, status = 200) =>
  new Response(JSON.stringify(data), {
    status,
    headers: { "Content-Type": "application/json" },
  });
afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});
function mockApi() {
  const fetch = vi.fn(async (url: string, init?: RequestInit) => {
    void init;
    if (url.includes("/transactions?")) return respond({ items: [{ id: 42 }] });
    if (url.endsWith("/transactions/42")) return respond({ id: 42, features });
    if (url.endsWith("/predict/explanation"))
      return respond({
        model_version: "verified-model",
        output_space: "probability",
        base_value: 0.1,
        caveat: "Anonymized features.",
        features: [{ feature: "V1", value: 1, contribution: 0.7 }],
      });
    return respond(prediction);
  });
  vi.stubGlobal("fetch", fetch);
  return fetch;
}
describe("schema-based prediction", () => {
  it("exposes exactly the documented 30 features and disables prediction without a model", () => {
    render(<PredictionForm models={null} />);
    expect(screen.getAllByRole("spinbutton")).toHaveLength(31);
    transactionFeatures.forEach((feature) =>
      expect(screen.getByLabelText(`Feature ${feature}`)).toBeInTheDocument(),
    );
    expect(
      screen.getByRole("button", { name: "Predict transaction" }),
    ).toBeDisabled();
  });
  it("loads a stored row, predicts with an explicit threshold, and explains the submitted snapshot", async () => {
    const fetch = mockApi();
    render(<PredictionForm models={models} />);
    fireEvent.click(
      screen.getByRole("button", { name: "Load stored example" }),
    );
    await waitFor(() =>
      expect(screen.getByLabelText("Feature Amount")).toHaveValue(29),
    );
    fireEvent.change(screen.getByLabelText("Decision threshold override"), {
      target: { value: "0.7" },
    });
    fireEvent.click(
      screen.getByRole("button", { name: "Predict transaction" }),
    );
    expect(await screen.findByText("80.0%")).toBeVisible();
    expect(screen.getByText(/Uncalibrated model estimate/)).toBeVisible();
    const predictionCall = fetch.mock.calls.find(([url]) =>
      url.endsWith("/predict"),
    );
    expect(JSON.parse(predictionCall![1]!.body as string)).toEqual({
      features,
      provenance: "synthetic",
      threshold: 0.7,
    });
    fireEvent.change(screen.getByLabelText("Feature V1"), {
      target: { value: "999" },
    });
    fireEvent.click(
      screen.getByRole("button", { name: "Explain prediction with SHAP" }),
    );
    expect(await screen.findByText(/SHAP output: probability/)).toBeVisible();
    const explanationCall = fetch.mock.calls.find(([url]) =>
      url.endsWith("/predict/explanation"),
    );
    expect(JSON.parse(explanationCall![1]!.body as string).features.V1).toBe(1);
  });
  it("shows missing examples and backend errors without fabricating a result", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(async () => respond({ detail: "No matching trained model" }, 409)),
    );
    render(<PredictionForm models={models} />);
    fireEvent.click(
      screen.getByRole("button", { name: "Load stored example" }),
    );
    expect(await screen.findByRole("alert")).toHaveTextContent(
      "No matching trained model",
    );
    expect(screen.queryByText("FRAUD CLASS PROBABILITY ESTIMATE")).toBeNull();
  });
  it("clears stale results when switching data source", async () => {
    mockApi();
    render(<PredictionForm models={models} />);
    fireEvent.click(
      screen.getByRole("button", { name: "Load stored example" }),
    );
    await waitFor(() =>
      expect(screen.getByLabelText("Feature Amount")).toHaveValue(29),
    );
    fireEvent.click(
      screen.getByRole("button", { name: "Predict transaction" }),
    );
    await screen.findByText("80.0%");
    fireEvent.change(screen.getByLabelText("Prediction data source"), {
      target: { value: "ulb" },
    });
    expect(screen.queryByText("80.0%")).toBeNull();
  });
});
