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
import type { Models } from "../types";
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
  const [models, setModels] = useState<Models | null>(null),
    [version, setVersion] = useState(""),
    [selected, setSelected] = useState(""),
    [view, setView] = useState("summary");
  useEffect(() => {
    api<Models>("/models")
      .then((d) => {
        setModels(d);
        setVersion(d.active_version ?? "");
      })
      .catch(fail);
  }, [revision]);
  const experiment = models?.experiments.find((e) => e.version === version),
    model =
      experiment?.models.find((m) => m.name === selected) ??
      experiment?.models.find((m) => m.name === experiment.selected_model);
  if (!models) return <Loading />;
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
                {e.provenance} · {e.version}
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
        <div className="table-wrap">
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
                {experiment.provenance === "synthetic"
                  ? "These results measure an artificial fixture. No ULB benchmark claim is made."
                  : "ULB is anonymized and covers a limited time window. Generalization to live banking systems is unverified."}
              </p>
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
