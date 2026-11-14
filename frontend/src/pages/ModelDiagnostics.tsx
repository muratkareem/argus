import { useState } from "react";
import {
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { percent } from "../api";
import { Empty, Panel } from "../ui";
import type { Model } from "../types";
const tooltip = {
  background: "#141e2c",
  border: "1px solid #2b3949",
  borderRadius: 8,
  color: "#dde6f1",
  fontSize: 12,
};

export function ModelDiagnostics({ model }: { model: Model }) {
  const [chosen, setChosen] = useState<number | null>(null);
  const analysis = model.validation_threshold_analysis;
  const point =
    analysis?.points.find((p) => p.threshold === chosen) ??
    analysis?.points.reduce((closest, p) =>
      Math.abs(p.threshold - model.threshold) <
      Math.abs(closest.threshold - model.threshold)
        ? p
        : closest,
    );
  return (
    <>
      <div className="two-grid">
        <Panel title={`${model.name} · ROC curve`}>
          <div className="chart-subtitle">
            Untouched test partition · false positive rate → · true positive
            rate ↑
          </div>
          {model.test.roc_curve ? (
            <div className="chart">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart
                  data={model.test.roc_curve}
                  margin={{ top: 10, right: 25, bottom: 10, left: -15 }}
                >
                  <CartesianGrid stroke="#202b38" />
                  <XAxis
                    type="number"
                    dataKey="false_positive_rate"
                    domain={[0, 1]}
                  />
                  <YAxis domain={[0, 1]} />
                  <Tooltip contentStyle={tooltip} />
                  <Line
                    isAnimationActive={false}
                    dataKey="true_positive_rate"
                    stroke="#64c2ba"
                    dot={false}
                    strokeWidth={2}
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>
          ) : (
            <Empty>
              ROC curve was not recorded in this experiment. Retrain to generate
              it.
            </Empty>
          )}
        </Panel>
        <Panel title="Calibration and inference">
          <div className="padded">
            <div className="detail-row">
              <span>Test false negative rate</span>
              <b>{percent(model.test.false_negative_rate)}</b>
            </div>
            <div className="detail-row">
              <span>Test Brier score (lower is better)</span>
              <b>{model.test.brier_score?.toFixed(6) ?? "Not recorded"}</b>
            </div>
            <div className="detail-row">
              <span>Warm single inference p95</span>
              <b>
                {model.inference_latency
                  ? `${model.inference_latency.single_p95_ms.toFixed(3)} ms`
                  : "Not recorded"}
              </b>
            </div>
            <div className="detail-row">
              <span>Warm batch of 1,000</span>
              <b>
                {model.inference_latency
                  ? `${model.inference_latency.batch_1000_ms.toFixed(3)} ms`
                  : "Not recorded"}
              </b>
            </div>
            <p className="muted">
              {model.inference_latency?.measurement ??
                "Latency measurements are unavailable for this historical artifact."}{" "}
              These model timings exclude HTTP and database work.
            </p>
            <p className="muted">
              Brier score assesses squared error of probability estimates. Class
              weighting and limited data can distort calibration; estimates
              remain labeled uncalibrated.
            </p>
            {model.test.calibration_curve && (
              <details>
                <summary>Observed calibration bins (test partition)</summary>
                <div className="table-wrap">
                  <table>
                    <thead>
                      <tr>
                        <th>Mean estimate</th>
                        <th>Observed fraud fraction</th>
                      </tr>
                    </thead>
                    <tbody>
                      {model.test.calibration_curve.map((p, i) => (
                        <tr key={i}>
                          <td>{percent(p.mean_predicted_probability)}</td>
                          <td>{percent(p.fraction_positive)}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </details>
            )}
          </div>
        </Panel>
      </div>
      <Panel
        title="Threshold trade-offs"
        meta={<span className="mini-tag">VALIDATION PARTITION ONLY</span>}
      >
        {analysis && point ? (
          <div className="padded">
            <p className="muted">
              The model threshold was selected using validation F1. Explore
              previously measured validation thresholds here; held-out test
              metrics remain fixed.
            </p>
            <label className="field">
              Validation threshold
              <select
                value={point.threshold}
                onChange={(e) => setChosen(Number(e.target.value))}
              >
                {analysis.points.map((p) => (
                  <option key={p.threshold} value={p.threshold}>
                    {p.threshold.toFixed(4)}
                    {p.threshold === model.threshold
                      ? " · selected model threshold"
                      : ""}
                  </option>
                ))}
              </select>
            </label>
            <div className="table-wrap">
              <table>
                <thead>
                  <tr>
                    <th>Precision</th>
                    <th>Recall</th>
                    <th>F1</th>
                    <th>False positives</th>
                    <th>False negatives</th>
                    <th>Illustrative cost</th>
                  </tr>
                </thead>
                <tbody>
                  <tr>
                    <td>{percent(point.precision)}</td>
                    <td>{percent(point.recall)}</td>
                    <td>{point.f1.toFixed(4)}</td>
                    <td>{point.false_positives}</td>
                    <td>{point.false_negatives}</td>
                    <td>{point.estimated_cost}</td>
                  </tr>
                </tbody>
              </table>
            </div>
            <p className="muted">
              Cost assumption: {analysis.cost_assumptions.false_positive} units
              per false positive + {analysis.cost_assumptions.false_negative}{" "}
              units per false negative. {analysis.cost_assumptions.unit}. These
              illustrative costs are not measured financial losses.
            </p>
          </div>
        ) : (
          <Empty>
            Validation threshold analysis was not recorded in this experiment.
          </Empty>
        )}
      </Panel>
    </>
  );
}
