import { useEffect, useState } from "react";
import { ArrowDownToLine } from "lucide-react";
import {
  Line,
  LineChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { api, download, percent } from "../api";
import { Panel, Empty, Loading } from "../ui";
import { ModelDiagnostics } from "./ModelDiagnostics";
import type { Models, BenchmarkCatalog } from "../types";
const tipStyle = {
  background: "#141e2c",
  border: "1px solid #2b3949",
  borderRadius: 8,
  color: "#dde6f1",
  fontSize: 12,
};
export default function Laboratory({
  revision,
  fail,
}: {
  revision: number;
  fail: (e: unknown) => void;
}) {
  const [models, setModels] = useState<Models | null>(null);
  const [catalog, setCatalog] = useState<BenchmarkCatalog | null>(null);
  const [dataset, setDataset] = useState("workspace");
  useEffect(() => {
    let active = true;
    Promise.all([api<Models>("/models"), api<BenchmarkCatalog>("/benchmarks")])
      .then(([workspace, benchmarks]) => {
        if (active) {
          setModels(workspace);
          setCatalog(benchmarks);
        }
      })
      .catch(fail);
    return () => {
      active = false;
    };
  }, [revision]);
  if (!models || !catalog) return <Loading />;
  const descriptor = catalog.datasets.find((d) => d.id === dataset);
  const experiments =
    dataset === "workspace"
      ? models.experiments
      : catalog.experiments.filter((e) => e.dataset_id === dataset);
  return (
    <>
      <label className="field">
        Dataset
        <select value={dataset} onChange={(e) => setDataset(e.target.value)}>
          <option value="workspace">Active workspace experiments</option>
          {catalog.datasets.map((d) => (
            <option key={d.id} value={d.id}>
              {d.name} · {d.data_kind} · {d.status.replaceAll("_", " ")}
            </option>
          ))}
        </select>
      </label>
      {descriptor && (
        <p className="muted">
          <a href={descriptor.source} target="_blank" rel="noreferrer">
            Official source
          </a>{" "}
          · {descriptor.license}.{" "}
          {descriptor.data_kind === "synthetic"
            ? "Simulation benchmark; not real transaction evidence."
            : "Real transaction dataset."}
        </p>
      )}
      <details className="padded">
        <summary>Verified dataset comparison</summary>
        <p>
          {catalog.interpretation} Scores differ in prevalence, feature
          availability and split design; they do not establish a ranking across
          domains.
        </p>
        <div
          className="table-wrap"
          role="region"
          aria-label="Verified dataset comparison"
          tabIndex={0}
        >
          <table>
            <thead>
              <tr>
                <th>Dataset / split</th>
                <th>Scope / seed</th>
                <th>Validation-selected model</th>
                <th>Test rows / fraud</th>
                <th>Test AP</th>
                <th>Test recall</th>
              </tr>
            </thead>
            <tbody>
              {catalog.experiments.map((e) => {
                const m = e.models.find((m) => m.name === e.selected_model)!;
                return (
                  <tr key={e.version}>
                    <td>
                      {e.dataset_id} · {e.data_kind} · {e.split}
                    </td>
                    <td>
                      {e.rows.toLocaleString()} rows · seed {e.seed}
                    </td>
                    <td>{m.name}</td>
                    <td>
                      {e.partitions.test.rows.toLocaleString()} /{" "}
                      {e.partitions.test.fraud}
                    </td>
                    <td>{m.test.average_precision.toFixed(4)}</td>
                    <td>{percent(m.test.recall)}</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
        {catalog.datasets
          .filter((d) => d.status !== "evaluated")
          .map((d) => (
            <p key={d.id}>
              {d.name}: {d.status.replaceAll("_", " ")}. {d.blocker}
            </p>
          ))}
      </details>
      {catalog.report_errors.length > 0 && (
        <p role="alert">
          {catalog.report_errors.length} invalid benchmark reports excluded.
          Check /api/v1/benchmarks report_errors.
        </p>
      )}
      {experiments.length ? (
        <ExperimentReview
          key={dataset}
          models={{
            active_version:
              dataset === "workspace"
                ? models.active_version
                : (
                    experiments.find(
                      (e) =>
                        e.source?.sampling === "full dataset" &&
                        e.seed === 42 &&
                        e.split === "chronological",
                    ) ?? experiments[0]
                  ).version,
            experiments,
          }}
        />
      ) : (
        <Empty>
          {descriptor?.blocker ?? "No executed experiments for this dataset."}{" "}
          No metrics are claimed. See docs/DATASETS.md for authorized
          reproduction commands.
        </Empty>
      )}
    </>
  );
}

function ExperimentReview({ models }: { models: Models }) {
  const [version, setVersion] = useState(
      models.active_version ?? models.experiments[0]?.version ?? "",
    ),
    [selected, setSelected] = useState(""),
    [view, setView] = useState("summary");
  const experiment = models?.experiments.find((e) => e.version === version),
    model =
      experiment?.models.find((m) => m.name === selected) ??
      experiment?.models.find((m) => m.name === experiment.selected_model);
  if (!experiment || !model)
    return (
      <Empty>
        No trained experiments. Run{" "}
        <code>PYTHONPATH=backend uv run python -m app.ml --synthetic</code> or
        train from an authorized ULB CSV.
      </Empty>
    );
  return (
    <>
      <div className="lab-toolbar">
        <label className="field">
          Experiment
          <select
            value={version}
            onChange={(e) => {
              setVersion(e.target.value);
              setSelected("");
            }}
          >
            {models.experiments.map((e) => (
              <option key={e.version} value={e.version}>
                {e.provenance} · {e.split} · {e.rows.toLocaleString()} rows ·
                seed {e.seed} · {e.version}
              </option>
            ))}
          </select>
        </label>
        <button
          className="secondary"
          onClick={() =>
            download(`argus-experiment-${version}.json`, experiment)
          }
        >
          <ArrowDownToLine size={14} />
          Export experiment JSON
        </button>
      </div>
      <div className="experiment-info">
        <span className="badge neutral">
          {experiment.provenance.toUpperCase()}
        </span>
        <span>{experiment.rows.toLocaleString()} rows</span>
        <span>{experiment.fraud_rows} fraud</span>
        <span>{experiment.split} split</span>
        <span>Seed {experiment.seed}</span>
        <span>{experiment.duplicates_removed} duplicates removed</span>
      </div>
      <Panel
        title="Model comparison"
        meta={
          <span className="muted">
            Click a model to inspect held-out results
          </span>
        }
      >
        <div
          className="table-wrap"
          role="region"
          aria-label="Model comparison results"
          tabIndex={0}
        >
          <table>
            <thead>
              <tr>
                <th>Algorithm</th>
                <th>Validation AP</th>
                <th>Test precision</th>
                <th>Test recall</th>
                <th>Test F1</th>
                <th>Test AP</th>
                <th>Test ROC-AUC</th>
              </tr>
            </thead>
            <tbody>
              {experiment.models.map((m) => (
                <tr
                  key={m.name}
                  className={model.name === m.name ? "selected-row" : ""}
                  onClick={() => setSelected(m.name)}
                >
                  <td>
                    <button
                      className="text-button"
                      onClick={() => setSelected(m.name)}
                    >
                      {m.name}
                    </button>
                    {m.name === experiment.selected_model && (
                      <small className="table-sub teal">
                        Selected by validation AP
                      </small>
                    )}
                  </td>
                  <td className="mono">
                    {m.validation_average_precision.toFixed(4)}
                  </td>
                  <td className="mono">{percent(m.test.precision)}</td>
                  <td className="mono">{percent(m.test.recall)}</td>
                  <td className="mono">{m.test.f1.toFixed(4)}</td>
                  <td className="mono">
                    {m.test.average_precision.toFixed(4)}
                  </td>
                  <td className="mono">{m.test.roc_auc.toFixed(4)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Panel>
      <div className="page-tabs" role="group" aria-label="Evaluation view">
        {[
          ["summary", "Test results"],
          ["diagnostics", "Calibration & thresholds"],
          ["methodology", "Features & methodology"],
        ].map(([id, label]) => (
          <button
            key={id}
            aria-pressed={view === id}
            className={view === id ? "active" : ""}
            onClick={() => setView(id)}
          >
            {label}
          </button>
        ))}
      </div>
      {experiment.source && (
        <p className="muted">
          Source: {experiment.source.rows.toLocaleString()} rows /{" "}
          {experiment.source.fraud_rows.toLocaleString()} fraud. Evaluation uses{" "}
          {experiment.rows.toLocaleString()} rows: {experiment.source.sampling}.{" "}
          {experiment.limitations}
        </p>
      )}
      {model.test.confidence_intervals && (
        <p className="muted">
          95% Wilson intervals · precision{" "}
          {model.test.confidence_intervals.precision?.map(percent).join("–") ??
            "undefined (no alerts)"}{" "}
          · recall{" "}
          {model.test.confidence_intervals.recall?.map(percent).join("–") ??
            "undefined"}
          . {model.test.confidence_intervals.limitation}
        </p>
      )}
      {model.test.day_cluster_bootstrap && (
        <p className="muted">
          Conditional day-cluster 95% intervals ·{" "}
          {model.test.day_cluster_bootstrap.clusters} days ·{" "}
          {model.test.day_cluster_bootstrap.repeats} replicates:
          {["average_precision", "f1", "roc_auc"].map((key) => (
            <span key={key}>
              {" "}
              {key.replaceAll("_", " ")} [
              {model.test.day_cluster_bootstrap?.intervals[key]
                ?.map((v) => v.toFixed(4))
                .join("–") ?? "undefined"}
              ] ·
            </span>
          ))}
          {model.test.day_cluster_bootstrap.limitation}
        </p>
      )}
      {view === "summary" && (
        <div className="two-grid">
          <Panel title={`${model.name} · Precision-recall`}>
            <div className="chart-subtitle">
              Held-out test data · threshold {model.threshold.toFixed(4)} · FPR{" "}
              {(model.test.false_positive_rate * 100).toFixed(3)}%
            </div>
            <div className="chart">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart
                  data={model.test.pr_curve}
                  margin={{ top: 10, right: 25, bottom: 10, left: -15 }}
                >
                  <CartesianGrid stroke="#202b38" />
                  <XAxis
                    type="number"
                    dataKey="recall"
                    domain={[0, 1]}
                    tickLine={false}
                  />
                  <YAxis domain={[0, 1]} tickLine={false} />
                  <Tooltip contentStyle={tipStyle} />
                  <Line
                    isAnimationActive={false}
                    dataKey="precision"
                    stroke="#64c2ba"
                    dot={false}
                    strokeWidth={2}
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>
            <div className="chart-foot">Recall → · Precision ↑</div>
          </Panel>
          <Panel
            title="Confusion matrix"
            meta={<span className="mini-tag">TEST PARTITION</span>}
          >
            <div className="confusion" aria-label="Confusion matrix values">
              <div />
              <span>Predicted clear</span>
              <span>Predicted fraud</span>
              <span>Actual clear</span>
              <b>
                {model.test.confusion_matrix[0][0]}
                <small>True negative</small>
              </b>
              <b className="warning">
                {model.test.confusion_matrix[0][1]}
                <small>False positive</small>
              </b>
              <span>Actual fraud</span>
              <b className="warning">
                {model.test.confusion_matrix[1][0]}
                <small>False negative</small>
              </b>
              <b>
                {model.test.confusion_matrix[1][1]}
                <small>True positive</small>
              </b>
            </div>
          </Panel>
        </div>
      )}
      {view === "diagnostics" && (
        <ModelDiagnostics key={`${version}-${model.name}`} model={model} />
      )}
      {view === "methodology" && (
        <div className="two-grid">
          <Panel title="Global feature importance">
            <div className="padded">
              {model.feature_importance.slice(0, 10).map((f) => (
                <div className="importance-row" key={f.feature}>
                  <code>{f.feature}</code>
                  <div>
                    <i
                      style={{
                        width: `${(f.importance / model.feature_importance[0].importance) * 100}%`,
                      }}
                    />
                  </div>
                  <span className="mono">{f.importance.toFixed(3)}</span>
                </div>
              ))}
              <p className="muted">
                Absolute standardized coefficients for logistic regression;
                impurity / split importance for tree models. These scales are
                not comparable across algorithms.
              </p>
            </div>
          </Panel>
          <Panel title="Experiment integrity">
            <div className="padded">
              {Object.entries(experiment.partitions).map(([name, p]) => (
                <div className="detail-row" key={name}>
                  <span>{name}</span>
                  <b>
                    {p.rows} rows · {p.fraud} fraud
                  </b>
                </div>
              ))}
              <p>
                Preprocessing is fitted on training data. Candidate parameters
                and decision thresholds are selected using validation data.
                Algorithm selection precedes test evaluation.
              </p>
              <p className="muted">
                {experiment.limitations ??
                  (experiment.provenance === "synthetic"
                    ? "These results measure an artificial fixture. No ULB benchmark claim is made."
                    : "ULB is anonymized and covers a limited time window. Generalization to live banking systems is unverified.")}
              </p>
              {experiment.preprocessing && (
                <p className="muted">
                  Predictors:{" "}
                  {[
                    ...experiment.preprocessing.numeric,
                    ...experiment.preprocessing.categorical,
                  ].join(", ")}
                  . Excluded: {experiment.preprocessing.excluded.join(", ")}.
                </p>
              )}
              <code>
                {new Date(experiment.created_at).toLocaleString()} ·{" "}
                {experiment.duration_seconds}s
              </code>
            </div>
          </Panel>
        </div>
      )}
    </>
  );
}
