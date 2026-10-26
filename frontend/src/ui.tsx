import type { ReactNode } from "react";
import { ChevronRight, Database, LoaderCircle } from "lucide-react";
import { amount, percent } from "./api";
import type { Tx } from "./types";
export function Risk({ tx }: { tx: Tx }) {
  return (
    <span
      className={
        "badge " +
        (tx.flagged == null ? "neutral" : tx.flagged ? "danger" : "success")
      }
    >
      {tx.flagged == null ? "Unscored" : tx.flagged ? "Flagged" : "Clear"}
    </span>
  );
}
export function Empty({ children }: { children: ReactNode }) {
  return (
    <div className="empty">
      <Database size={26} />
      <p>{children}</p>
    </div>
  );
}
export function Panel({
  title,
  meta,
  children,
  className = "",
}: {
  title: string;
  meta?: ReactNode;
  children: ReactNode;
  className?: string;
}) {
  return (
    <section className={"panel " + className}>
      <div className="panel-head">
        <h2>{title}</h2>
        {meta}
      </div>
      {children}
    </section>
  );
}
export function Metric({
  label,
  value,
  detail,
  accent = false,
}: {
  label: string;
  value: ReactNode;
  detail: ReactNode;
  accent?: boolean;
}) {
  return (
    <div className={"metric " + (accent ? "metric-accent" : "")}>
      <span>{label}</span>
      <strong>{value}</strong>
      <small>{detail}</small>
    </div>
  );
}
export function TxTable({
  items,
  onSelect,
}: {
  items: Tx[];
  onSelect: (id: number) => void;
}) {
  return items.length ? (
    <div className="table-wrap">
      <table>
        <thead>
          <tr>
            <th>Transaction</th>
            <th>
              Amount <span className="unit">units</span>
            </th>
            <th>Risk score</th>
            <th>Assessment</th>
            <th>Source</th>
            <th />
          </tr>
        </thead>
        <tbody>
          {items.map((tx) => (
            <tr key={tx.id} onClick={() => onSelect(tx.id)}>
              <td>
                <button
                  className="text-button mono"
                  onClick={(e) => {
                    e.stopPropagation();
                    onSelect(tx.id);
                  }}
                >
                  TX-{String(tx.id).padStart(6, "0")}
                </button>
                <small className="table-sub">
                  T + {Math.floor(tx.time / 3600)}h{" "}
                  {Math.floor((tx.time % 3600) / 60)}m
                </small>
              </td>
              <td className="mono">{amount(tx.amount)}</td>
              <td>
                <div className="risk-value">
                  <span className="mono">{percent(tx.risk_score)}</span>
                  <div className="risk-track">
                    <i
                      style={{
                        width: `${(tx.risk_score ?? 0) * 100}%`,
                        background: tx.flagged ? "#f47974" : "#51aaa7",
                      }}
                    />
                  </div>
                </div>
              </td>
              <td>
                <Risk tx={tx} />
              </td>
              <td>
                <span className="source-dot" />
                {tx.provenance === "synthetic" ? "Synthetic" : "ULB benchmark"}
              </td>
              <td>
                <ChevronRight size={15} />
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  ) : (
    <Empty>No matching transactions. Import a CSV to get started.</Empty>
  );
}

export function Loading() {
  return (
    <div className="loading">
      <LoaderCircle className="spin" size={20} />
      Loading workspace data…
    </div>
  );
}
