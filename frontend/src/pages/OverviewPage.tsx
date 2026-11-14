import { useEffect, useState } from "react";
import { ArrowRight, Database, ShieldCheck } from "lucide-react";
import {
  Area,
  AreaChart,
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { api, percent } from "../api";
import { Panel, Metric, TxTable, Empty, Loading } from "../ui";
import type { Case, ActiveModel, Overview } from "../types";
const nav = (page: string) => {
  location.hash = page;
};
const tipStyle = {
  background: "#141e2c",
  border: "1px solid #2b3949",
  borderRadius: 8,
  color: "#dde6f1",
  fontSize: 12,
};
export default function OverviewPage({
  revision,
  activeModel,
  onSelect,
  fail,
}: {
  revision: number;
  activeModel?: ActiveModel;
  onSelect: (id: number) => void;
  fail: (e: unknown) => void;
}) {
  const [data, setData] = useState<Overview | null>(null),
    [recentCases, setRecentCases] = useState<Case[]>([]),
    [riskBand, setRiskBand] = useState(9);
  useEffect(() => {
    api<Overview>("/overview").then(setData).catch(fail);
    api<Case[]>("/cases").then(setRecentCases).catch(fail);
  }, [revision]);
  if (!data) return <Loading />;
  const model = activeModel?.status === "ready" ? activeModel : null;
  return (
    <>
      <div className="section-kicker">
        <span>
          <span className="online-dot" /> LIVE WORKSPACE SNAPSHOT
        </span>
        <span className="mono">
          {data.scored.toLocaleString()} scored / {data.total.toLocaleString()}{" "}
          stored
        </span>
      </div>
      <div className="metrics-grid">
        <Metric
          label="TOTAL TRANSACTIONS"
          value={data.total.toLocaleString()}
          detail={
            <>
              <Database size={12} />
              {Object.entries(data.provenance_counts)
                .map(([p, n]) => `${n} ${p}`)
                .join(" · ") || "No datasets imported"}
            </>
          }
        />
        <Metric
          label="FLAGGED FOR REVIEW"
          value={data.flagged.toLocaleString()}
          accent
          detail={
            <>
              <span className="tiny-dot red" />
              {percent(data.scored ? data.flagged / data.scored : null)} of
              scored transactions
            </>
          }
        />
        <Metric
          label="OBSERVED FRAUD"
          value={data.labeled_fraud ?? "—"}
          detail={
            <>
              {data.labeled_legitimate ?? "—"} labeled legitimate ·{" "}
              {data.unlabeled ?? "—"} unlabeled
            </>
          }
        />
        <Metric
          label="OPEN INVESTIGATIONS"
          value={data.open_cases}
          detail={
            <button
              className="text-button"
              onClick={() => nav("investigations")}
            >
              View investigation queue <ArrowRight size={12} />
            </button>
          }
        />
      </div>
      <div className="lower-grid">
        <Panel
          title="Flagged transactions"
          meta={
            <button className="text-button" onClick={() => nav("transactions")}>
              View explorer <ArrowRight size={13} />
            </button>
          }
        >
          <div className="chart-subtitle">
            Most recently imported records requiring analyst review
          </div>
          <TxTable
            items={data.recent_flagged.slice(0, 5)}
            onSelect={onSelect}
          />
        </Panel>
        <Panel
          title="Detection model"
          meta={
            <span className="status-dot-label">
              {model && <span className="online-dot" />}
              {model ? "ACTIVE" : "UNAVAILABLE"}
            </span>
          }
        >
          {model ? (
            <div className="model-card">
              <h3>{model.name}</h3>
              <div className="model-stat">
                <span>Training source</span>
                <b>{model.provenance?.toUpperCase()}</b>
              </div>
              <div className="model-stat">
                <span>Review threshold</span>
                <b>{percent(model.threshold)}</b>
              </div>
              <p className="muted">
                Class estimates are uncalibrated. Review flags alongside
                observed labels.
              </p>
              <a className="secondary full" href="#laboratory">
                Model performance <ArrowRight size={14} />
              </a>
            </div>
          ) : (
            <Empty>No active model metadata available.</Empty>
          )}
        </Panel>
      </div>
      <div className="chart-grid">
        <Panel
          title="Transaction activity"
          meta={
            <span className="legend">
              <i />
              All transactions <i className="red" />
              Flagged
            </span>
          }
        >
          <div className="chart-subtitle">
            Transaction count by hour from dataset start
          </div>
          {data.trend.length ? (
            <div className="chart">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart
                  data={data.trend}
                  onClick={(state) => {
                    if (state?.activeLabel != null) {
                      const hour = Number(state.activeLabel);
                      nav(
                        `transactions?min_time=${hour * 3600}&max_time=${(hour + 1) * 3600 - 0.001}`,
                      );
                    }
                  }}
                  margin={{ top: 14, right: 20, bottom: 0, left: -24 }}
                >
                  <defs>
                    <linearGradient id="area" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="0%" stopColor="#4f9baa" stopOpacity={0.3} />
                      <stop offset="100%" stopColor="#4f9baa" stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid stroke="#202b38" vertical={false} />
                  <XAxis
                    dataKey="hour"
                    tickFormatter={(v) => `${v}h`}
                    tickLine={false}
                    axisLine={false}
                    minTickGap={40}
                  />
                  <YAxis
                    tickFormatter={(value: number) =>
                      value >= 1000 ? `${value / 1000}k` : String(value)
                    }
                    tickLine={false}
                    axisLine={false}
                  />
                  <Tooltip
                    contentStyle={tipStyle}
                    labelFormatter={(v) => `Hour ${v}`}
                  />
                  <Area
                    isAnimationActive={false}
                    type="monotone"
                    dataKey="count"
                    stroke="#5bb5b7"
                    fill="url(#area)"
                    strokeWidth={2}
                  />
                  <Area
                    isAnimationActive={false}
                    type="monotone"
                    dataKey="flagged"
                    stroke="#f47974"
                    fill="transparent"
                    strokeWidth={1.5}
                  />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          ) : (
            <Empty>Import data to view transaction activity.</Empty>
          )}
          <div className="chart-foot">
            <span>Dataset time · 1 hour intervals</span>
            <span className="mono">{data.trend.length} active intervals</span>
          </div>
        </Panel>
        <Panel
          title="Risk distribution"
          meta={<span className="mini-tag">MODEL SCORES</span>}
        >
          <div className="chart-subtitle">
            Uncalibrated score · {data.scored} transactions
          </div>
          <div className="chart">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart
                data={data.risk_distribution}
                margin={{ top: 14, right: 14, bottom: 0, left: -24 }}
              >
                <CartesianGrid stroke="#202b38" vertical={false} />
                <XAxis
                  dataKey="bucket"
                  interval={2}
                  tickLine={false}
                  axisLine={false}
                />
                <YAxis
                  tickFormatter={(value: number) =>
                    value >= 1000 ? `${value / 1000}k` : String(value)
                  }
                  tickLine={false}
                  axisLine={false}
                />
                <Tooltip contentStyle={tipStyle} />
                <Bar
                  isAnimationActive={false}
                  dataKey="count"
                  onClick={(_data, index) =>
                    nav(
                      `transactions?min_risk=${index / 10}&max_risk=${(index + 1) / 10}`,
                    )
                  }
                  style={{ cursor: "pointer" }}
                  fill="#42968f"
                  radius={[3, 3, 0, 0]}
                  maxBarSize={24}
                />
              </BarChart>
            </ResponsiveContainer>
          </div>
          <div className="chart-foot">
            <label className="risk-band-control">
              Inspect range
              <select
                aria-label="Risk band to explore"
                value={riskBand}
                onChange={(e) => setRiskBand(Number(e.target.value))}
              >
                {data.risk_distribution.map((b, index) => (
                  <option key={b.bucket} value={index}>
                    {b.bucket}
                  </option>
                ))}
              </select>
            </label>
            <button
              className="text-button"
              onClick={() =>
                nav(
                  `transactions?min_risk=${riskBand / 10}&max_risk=${(riskBand + 1) / 10}`,
                )
              }
            >
              Explore range <ArrowRight size={11} />
            </button>
          </div>
        </Panel>
      </div>
      {recentCases.length > 0 && (
        <Panel
          title="Recent investigations"
          meta={
            <button
              className="text-button"
              onClick={() => nav("investigations")}
            >
              Open workbench <ArrowRight size={12} />
            </button>
          }
        >
          {recentCases.length ? (
            <div className="case-watchlist">
              {recentCases.slice(0, 4).map((c) => (
                <a key={c.id} href={`#investigations/${c.id}`}>
                  <span className="mono">
                    CASE-{String(c.id).padStart(4, "0")}
                  </span>
                  <b>{c.title}</b>
                  <span>
                    <i
                      className={
                        "badge " +
                        (["Critical", "High"].includes(c.priority)
                          ? "danger"
                          : "neutral")
                      }
                    >
                      {c.priority}
                    </i>
                    <small>{c.status}</small>
                  </span>
                </a>
              ))}
            </div>
          ) : (
            <Empty>
              No investigations yet. Start from a flagged transaction.
            </Empty>
          )}
        </Panel>
      )}
      <div className="insight-bar">
        <ShieldCheck size={19} />
        <span>
          <b>
            Labeled-data detection rate: {percent(data.fraud_detection_rate)}
          </b>
          <small>
            Observed labels: {data.labeled_fraud ?? "—"} fraud,{" "}
            {data.labeled_legitimate ?? "—"} legitimate, {data.unlabeled ?? "—"}{" "}
            unlabeled. Computed over {data.labeled_scored_fraud} labeled fraud
            records with stored scores. This is an operational view, separate
            from held-out test evaluation.
          </small>
        </span>
      </div>
    </>
  );
}
