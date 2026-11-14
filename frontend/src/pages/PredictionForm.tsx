import { useEffect, useState } from "react";
import { FlaskConical, LoaderCircle, ShieldCheck } from "lucide-react";
import { api, percent, send } from "../api";
import { Empty, Panel } from "../ui";
import type { Models, Tx } from "../types";

export const transactionFeatures = [
  "Time",
  ...Array.from({ length: 28 }, (_, i) => `V${i + 1}`),
  "Amount",
];
type PredictionInput = {
  features: Record<string, number>;
  provenance: string;
  threshold?: number;
};
type Prediction = {
  model_version: string;
  model_name: string;
  risk_score: number;
  classification: string;
  risk_category: string;
  decision_threshold: number;
  metadata: { processing_ms: number; score_type: string };
};
type Explanation = {
  model_version: string;
  output_space: string;
  base_value: number;
  caveat: string;
  features: { feature: string; contribution: number; value: number }[];
};

export function PredictionForm({ models }: { models: Models | null }) {
  const [values, setValues] = useState<Record<string, string>>({}),
    [provenance, setProvenance] = useState("synthetic"),
    [threshold, setThreshold] = useState(""),
    [result, setResult] = useState<Prediction | null>(null),
    [submitted, setSubmitted] = useState<PredictionInput | null>(null),
    [explanation, setExplanation] = useState<Explanation | null>(null),
    [busy, setBusy] = useState(""),
    [error, setError] = useState("");
  useEffect(() => {
    const experiment = models?.experiments.find(
      (e) => e.version === models.active_version,
    );
    if (experiment) setProvenance(experiment.provenance);
  }, [models]);
  async function loadExample() {
    setBusy("example");
    setError("");
    setResult(null);
    setExplanation(null);
    try {
      const rows = await api<{ items: Tx[] }>(
        `/transactions?provenance=${provenance}&page_size=1&sort=id&direction=asc`,
      );
      if (!rows.items.length)
        throw new Error(
          "No stored transactions for this source. Import a CSV or enter all features.",
        );
      const tx = await api<Tx>(`/transactions/${rows.items[0].id}`);
      setValues(
        Object.fromEntries(
          Object.entries(tx.features ?? {}).map(([k, v]) => [k, String(v)]),
        ),
      );
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy("");
    }
  }
  async function predict(event: React.FormEvent) {
    event.preventDefault();
    setError("");
    setResult(null);
    setExplanation(null);
    const features = Object.fromEntries(
      transactionFeatures.map((f) => [f, Number(values[f])]),
    );
    if (
      transactionFeatures.some(
        (f) => !values[f]?.trim() || !Number.isFinite(features[f]),
      )
    ) {
      setError("Enter a finite numeric value for each of the 30 features.");
      return;
    }
    const input: PredictionInput = {
      features,
      provenance,
      ...(threshold.trim() ? { threshold: Number(threshold) } : {}),
    };
    setBusy("prediction");
    try {
      setResult(await api<Prediction>("/predict", send("POST", input)));
      setSubmitted(input);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy("");
    }
  }
  async function explain() {
    if (!submitted) return;
    setBusy("explanation");
    setError("");
    try {
      setExplanation(
        await api<Explanation>("/predict/explanation", send("POST", submitted)),
      );
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy("");
    }
  }
  return (
    <div className="two-grid prediction-workspace">
      <Panel title="Single transaction prediction">
        <form className="padded" onSubmit={predict}>
          <p className="muted" id="feature-schema-help">
            Enter Time (seconds from dataset start), Amount (source units), and
            anonymized V1–V28. Load a stored row to inspect an input from the
            selected source. Predictions here are not saved.
          </p>
          <div className="prediction-controls">
            <label className="field">
              Prediction data source
              <select
                value={provenance}
                onChange={(e) => {
                  setProvenance(e.target.value);
                  setResult(null);
                  setExplanation(null);
                }}
              >
                <option value="synthetic">Synthetic demonstration data</option>
                <option value="ulb">ULB benchmark data</option>
              </select>
            </label>
            <label className="field">
              Decision threshold override
              <input
                type="number"
                min="0"
                max="1"
                step="any"
                value={threshold}
                placeholder="Validated model threshold"
                onChange={(e) => setThreshold(e.target.value)}
              />
            </label>
          </div>
          <button
            type="button"
            className="secondary"
            disabled={!!busy}
            onClick={loadExample}
          >
            {busy === "example" && <LoaderCircle size={14} className="spin" />}
            Load stored example
          </button>
          <details className="prediction-features" open>
            <summary>30 required transaction features</summary>
            <div
              className="prediction-feature-grid"
              aria-describedby="feature-schema-help"
            >
              {transactionFeatures.map((f) => (
                <label className="field" key={f}>
                  {f}
                  <input
                    aria-label={`Feature ${f}`}
                    type="number"
                    step="any"
                    min={f === "Time" || f === "Amount" ? 0 : undefined}
                    required
                    value={values[f] ?? ""}
                    onChange={(e) =>
                      setValues((previous) => ({
                        ...previous,
                        [f]: e.target.value,
                      }))
                    }
                  />
                </label>
              ))}
            </div>
          </details>
          <button
            className="primary"
            type="submit"
            disabled={!!busy || !models?.active_version}
          >
            {busy === "prediction" ? (
              <LoaderCircle size={14} className="spin" />
            ) : (
              <ShieldCheck size={14} />
            )}
            Predict transaction
          </button>
          {!models?.active_version && (
            <p className="muted">
              Train a model before requesting a prediction.
            </p>
          )}
          {error && (
            <div role="alert" className="error-text prediction-error">
              {error}
            </div>
          )}
        </form>
      </Panel>
      <Panel title="Prediction result">
        {result ? (
          <div className="padded" aria-live="polite">
            <div className="detail-score">
              <span>FRAUD CLASS PROBABILITY ESTIMATE</span>
              <strong>{percent(result.risk_score)}</strong>
              <small>
                Uncalibrated model estimate · not certainty of fraud
              </small>
            </div>
            <div className="detail-row">
              <span>Review classification</span>
              <b>{result.classification}</b>
            </div>
            <div className="detail-row">
              <span>Risk category</span>
              <b>{result.risk_category}</b>
            </div>
            <div className="detail-row">
              <span>Applied threshold</span>
              <b>{result.decision_threshold.toFixed(4)}</b>
            </div>
            <div className="detail-row">
              <span>Algorithm</span>
              <b>{result.model_name}</b>
            </div>
            <div className="detail-row">
              <span>Model version</span>
              <code>{result.model_version}</code>
            </div>
            <div className="detail-row">
              <span>Processing time</span>
              <b>{result.metadata.processing_ms.toFixed(2)} ms</b>
            </div>
            <p className="muted">
              Threshold overrides demonstrate alert trade-offs; they do not
              change validated test results.
            </p>
            <button className="secondary" disabled={!!busy} onClick={explain}>
              {busy === "explanation" ? (
                <LoaderCircle size={14} className="spin" />
              ) : (
                <FlaskConical size={14} />
              )}
              Explain prediction with SHAP
            </button>
            {explanation && (
              <div className="explanation">
                {explanation.model_version !== result.model_version && (
                  <p role="alert" className="error-text">
                    The active model changed. This explanation uses{" "}
                    {explanation.model_version}; request a fresh prediction to
                    compare.
                  </p>
                )}
                <p className="muted">
                  SHAP output: {explanation.output_space}. Base value:{" "}
                  {explanation.base_value.toFixed(4)}.
                </p>
                <p className="muted">
                  Positive contributions increase model output; negative
                  contributions decrease it.
                </p>
                {explanation.features.slice(0, 10).map((f) => (
                  <div className="detail-row" key={f.feature}>
                    <code>{f.feature}</code>
                    <b className={f.contribution > 0 ? "red" : "teal"}>
                      {f.contribution > 0 ? "+" : ""}
                      {f.contribution.toFixed(4)}
                    </b>
                  </div>
                ))}
                <p className="muted">
                  {explanation.caveat} Contributions describe model behavior,
                  not causal evidence.
                </p>
              </div>
            )}
          </div>
        ) : (
          <Empty>
            Submit a transaction to view its model estimate, review
            classification, and explanation.
          </Empty>
        )}
      </Panel>
    </div>
  );
}
