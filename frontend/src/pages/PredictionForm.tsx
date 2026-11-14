import { useEffect, useState } from "react";
import { ArrowRight, LoaderCircle, ShieldCheck } from "lucide-react";
import { api, percent, send } from "../api";
import { Empty, Panel } from "../ui";
import { ExplanationContributions } from "../components/ExplanationContributions";
import type { Contribution } from "../components/ExplanationContributions";
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
  features: Contribution[];
};

export function PredictionForm({ models }: { models: Models | null }) {
  const [values, setValues] = useState<Record<string, string>>({});
  const [provenance, setProvenance] = useState("synthetic");
  const [threshold, setThreshold] = useState("");
  const [result, setResult] = useState<Prediction | null>(null);
  const [submitted, setSubmitted] = useState<PredictionInput | null>(null);
  const [explanation, setExplanation] = useState<Explanation | null>(null);
  const [busy, setBusy] = useState("");
  const [error, setError] = useState("");
  const [loadedId, setLoadedId] = useState<number | null>(null);
  const transactionId = new URLSearchParams(
    location.hash.split("?")[1] ?? "",
  ).get("transaction");
  useEffect(() => {
    const experiment = models?.experiments.find(
      (e) => e.version === models.active_version,
    );
    if (experiment && !transactionId) setProvenance(experiment.provenance);
  }, [models, transactionId]);
  useEffect(() => {
    if (!transactionId) return;
    let cancelled = false;
    setBusy("example");
    api<Tx>(`/transactions/${encodeURIComponent(transactionId)}`)
      .then((tx) => {
        if (cancelled) return;
        setValues(
          Object.fromEntries(
            Object.entries(tx.features ?? {}).map(([k, v]) => [k, String(v)]),
          ),
        );
        setProvenance(tx.provenance);
        setLoadedId(tx.id);
        setResult(null);
        setExplanation(null);
      })
      .catch((e) => {
        if (!cancelled) setError(e.message);
      })
      .finally(() => {
        if (!cancelled) setBusy("");
      });
    return () => {
      cancelled = true;
    };
  }, [transactionId]);
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
      setLoadedId(tx.id);
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
      setError(
        "Load a stored transaction or enter a finite numeric value for each of the 30 features.",
      );
      return;
    }
    if (features.Time < 0 || features.Amount < 0) {
      setError("Time and Amount must be nonnegative.");
      return;
    }
    if (
      threshold.trim() &&
      (!Number.isFinite(Number(threshold)) ||
        Number(threshold) < 0 ||
        Number(threshold) > 1)
    ) {
      setError("Choose a decision threshold between 0 and 1.");
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
  function field(feature: string) {
    return (
      <label className="field" key={feature}>
        {feature}
        <input
          type="number"
          step="any"
          min={feature === "Time" || feature === "Amount" ? 0 : undefined}
          aria-label={`Feature ${feature}`}
          value={values[feature] ?? ""}
          onChange={(e) =>
            setValues((v) => ({ ...v, [feature]: e.target.value }))
          }
        />
      </label>
    );
  }
  const ready = transactionFeatures.filter(
    (f) => values[f]?.trim() && Number.isFinite(Number(values[f])),
  ).length;
  return (
    <div className="two-grid prediction-workspace">
      <Panel title="Single transaction prediction">
        <form className="padded" onSubmit={predict} noValidate>
          <div className="form-step">
            <span>01</span>
            <div>
              <h3>Choose a transaction</h3>
              <p>
                Start with a stored example, or enter the exact model inputs.
              </p>
            </div>
          </div>
          <label className="field">
            Prediction data source
            <select
              value={provenance}
              onChange={(e) => {
                setProvenance(e.target.value);
                setResult(null);
                setExplanation(null);
                setLoadedId(null);
                setValues({});
              }}
            >
              <option value="synthetic">Synthetic demonstration data</option>
              <option value="ulb">ULB benchmark data</option>
            </select>
          </label>
          <div className="example-actions">
            <button
              type="button"
              className="secondary"
              disabled={!!busy}
              onClick={loadExample}
            >
              {busy === "example" ? (
                <LoaderCircle className="spin" size={15} />
              ) : (
                <ArrowRight size={15} />
              )}
              Load stored example
            </button>
            <a className="text-button" href="#transactions">
              Browse transactions
            </a>
          </div>
          {loadedId != null && (
            <p className="loaded-record" role="status">
              Loaded TX-{String(loadedId).padStart(6, "0")} · {ready}/30 valid
              inputs
            </p>
          )}
          <div className="prediction-controls core-inputs">
            {field("Time")}
            {field("Amount")}
          </div>
          <details className="prediction-features">
            <summary>Advanced features · V1–V28</summary>
            <p className="muted">
              Anonymized PCA components. Keep their original names and values;
              no merchant or cardholder meaning is inferred.
            </p>
            <div className="prediction-feature-grid">
              {transactionFeatures.filter((f) => f.startsWith("V")).map(field)}
            </div>
          </details>
          <details className="decision-settings">
            <summary>Decision settings</summary>
            <label className="field">
              Decision threshold override
              <input
                type="number"
                min="0"
                max="1"
                step="any"
                value={threshold}
                placeholder="Use validated model threshold"
                onChange={(e) => setThreshold(e.target.value)}
              />
            </label>
            <p className="muted">
              An override changes the review decision, not the probability
              estimate or saved model.
            </p>
          </details>
          <button
            className="primary full"
            disabled={!!busy || !models?.active_version}
            type="submit"
          >
            {busy === "prediction" ? (
              <LoaderCircle size={16} className="spin" />
            ) : (
              <ShieldCheck size={16} />
            )}
            Predict transaction
          </button>
          {!models?.active_version && (
            <p className="muted">
              A trained model is required. Check System Information.
            </p>
          )}
          {error && (
            <div className="prediction-error" role="alert">
              {error}
            </div>
          )}
        </form>
      </Panel>
      <Panel title="Prediction result">
        {result ? (
          <div className="padded">
            <div className="prediction-outcome">
              <span className="outcome-label">
                FRAUD CLASS PROBABILITY ESTIMATE
              </span>
              <strong>{percent(result.risk_score)}</strong>
              <span
                className={
                  "badge " +
                  (result.classification === "flagged" ? "danger" : "success")
                }
              >
                {result.classification === "flagged"
                  ? "Flagged for review"
                  : "Below review threshold"}
              </span>
              <p>Uncalibrated model estimate · not certainty of fraud</p>
            </div>
            <div className="detail-row">
              <span>Risk category</span>
              <b>{result.risk_category}</b>
            </div>
            <div className="detail-row">
              <span>Applied threshold</span>
              <b>{percent(result.decision_threshold)}</b>
            </div>
            <div className="detail-row">
              <span>Algorithm</span>
              <b>{result.model_name}</b>
            </div>
            <button
              type="button"
              className="secondary full"
              disabled={!!busy}
              onClick={explain}
            >
              {busy === "explanation" && (
                <LoaderCircle size={15} className="spin" />
              )}
              Explain prediction with SHAP
            </button>
            {explanation && (
              <ExplanationContributions
                features={explanation.features}
                outputSpace={explanation.output_space}
                baseValue={explanation.base_value}
                modelVersion={explanation.model_version}
                caveat={explanation.caveat}
              />
            )}
            <details className="technical-details">
              <summary>Prediction metadata</summary>
              <div className="detail-row">
                <span>Model version</span>
                <code>{result.model_version}</code>
              </div>
              <p>
                {result.metadata.score_type} ·{" "}
                {result.metadata.processing_ms.toFixed(2)} ms
              </p>
            </details>
            {loadedId != null && (
              <a className="text-button" href="#investigations">
                Continue to investigations <ArrowRight size={14} />
              </a>
            )}
          </div>
        ) : (
          <div className="prediction-placeholder">
            <ShieldCheck size={32} />
            <h3>Your review starts here</h3>
            <p>
              Choose a transaction and run a prediction to see its score, review
              decision, and explanation.
            </p>
            <Empty>No prediction submitted</Empty>
          </div>
        )}
      </Panel>
    </div>
  );
}
