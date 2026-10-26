import { useEffect, useState } from "react";
import {
  ArrowDownToLine,
  ChevronLeft,
  ChevronRight,
  Search,
  Save,
  Trash2,
  RotateCcw,
} from "lucide-react";
import { api, send } from "../api";
import { Panel, TxTable, Loading } from "../ui";
import type { Tx } from "../types";
const defaults = {
  q: "",
  flagged: "all",
  provenance: "all",
  sort: "risk_score",
  direction: "desc",
  min_risk: "",
  max_risk: "",
  min_amount: "",
  max_amount: "",
  min_time: "",
  max_time: "",
  label: "all",
};
type Filters = typeof defaults;
type View = {
  id: number;
  name: string;
  filters: Record<string, string | number | boolean>;
};
function filtersFromLocation(): Filters {
  const next = { ...defaults };
  const query = new URLSearchParams(location.hash.split("?")[1] ?? "");
  for (const [key, value] of query)
    if (key in next) next[key as keyof Filters] = value;
  return next;
}
export function TransactionIntelligence({
  revision,
  onSelect,
  fail,
}: {
  revision: number;
  onSelect: (id: number) => void;
  fail: (e: unknown) => void;
}) {
  const [filters, setFilters] = useState<Filters>(filtersFromLocation),
    [page, setPage] = useState(1),
    [data, setData] = useState<{ items: Tx[]; total: number } | null>(null),
    [views, setViews] = useState<View[]>([]),
    [viewId, setViewId] = useState(""),
    [name, setName] = useState(""),
    [saving, setSaving] = useState(false);
  const params = new URLSearchParams(
    Object.entries(filters).filter(([, v]) => v !== "" && v !== "all"),
  );
  const key = params.toString();
  const set = (field: keyof Filters, value: string) => {
    setFilters((f) => ({ ...f, [field]: value }));
    setPage(1);
    setViewId("");
  };
  const loadViews = () => api<View[]>("/views").then(setViews).catch(fail);
  useEffect(() => {
    const change = () => {
      setFilters(filtersFromLocation());
      setPage(1);
      setViewId("");
    };
    addEventListener("hashchange", change);
    return () => removeEventListener("hashchange", change);
  }, []);
  useEffect(() => {
    void loadViews();
  }, []);
  useEffect(() => {
    let cancelled = false;
    const timer = setTimeout(
      () =>
        api<{ items: Tx[]; total: number }>(
          `/transactions?${key}&page=${page}&page_size=20`,
        )
          .then((result) => {
            if (!cancelled) setData(result);
          })
          .catch(fail),
      180,
    );
    return () => {
      cancelled = true;
      clearTimeout(timer);
    };
  }, [key, page, revision]);
  async function save() {
    setSaving(true);
    try {
      const config: Record<string, string | number | boolean> = {};
      for (const [k, v] of params) {
        config[k] = ["flagged"].includes(k)
          ? v === "true"
          : ["q", "sort", "direction", "provenance"].includes(k)
            ? v
            : Number(v);
      }
      const saved = await api<View>(
        "/views",
        send("POST", { name, filters: config }),
      );
      await loadViews();
      setViewId(String(saved.id));
      setName("");
    } catch (e) {
      fail(e);
    } finally {
      setSaving(false);
    }
  }
  function apply(id: string) {
    setViewId(id);
    const found = views.find((v) => v.id === Number(id));
    if (found) {
      const next = { ...defaults };
      for (const [k, v] of Object.entries(found.filters))
        if (k in next) next[k as keyof Filters] = String(v);
      setFilters(next);
      setPage(1);
    }
  }
  async function remove() {
    try {
      await api(`/views/${viewId}`, { method: "DELETE" });
      setViewId("");
      await loadViews();
    } catch (e) {
      fail(e);
    }
  }
  const active = Object.entries(filters).filter(
    ([k, v]) =>
      !["sort", "direction", "q"].includes(k) && v !== "" && v !== "all",
  );
  return (
    <div className="transaction-intelligence">
      <aside className="filter-rail">
        <div className="rail-heading">
          QUERY BUILDER
          <button
            className="icon-button"
            aria-label="Reset transaction filters"
            onClick={() => {
              setFilters(defaults);
              setPage(1);
              setViewId("");
            }}
          >
            <RotateCcw size={12} />
          </button>
        </div>
        <label className="field">
          Saved views
          <select
            aria-label="Saved transaction views"
            value={viewId}
            onChange={(e) => apply(e.target.value)}
          >
            <option value="">Unsaved query</option>
            {views.map((v) => (
              <option key={v.id} value={v.id}>
                {v.name}
              </option>
            ))}
          </select>
        </label>
        {viewId && (
          <button className="text-button" onClick={remove}>
            <Trash2 size={12} />
            Delete saved view
          </button>
        )}
        <label className="field">
          Assessment
          <select
            aria-label="Assessment filter"
            value={filters.flagged}
            onChange={(e) => set("flagged", e.target.value)}
          >
            <option value="all">All assessments</option>
            <option value="true">Flagged only</option>
            <option value="false">Clear only</option>
          </select>
        </label>
        <label className="field">
          Data provenance
          <select
            aria-label="Data source filter"
            value={filters.provenance}
            onChange={(e) => set("provenance", e.target.value)}
          >
            <option value="all">All sources</option>
            <option value="ulb">ULB benchmark</option>
            <option value="synthetic">Synthetic</option>
          </select>
        </label>
        <div className="filter-group-label">MODEL SCORE RANGE · 0–1</div>
        <div className="range-fields">
          <input
            type="number"
            min="0"
            max="1"
            step=".01"
            aria-label="Minimum risk score"
            placeholder="Min"
            value={filters.min_risk}
            onChange={(e) => set("min_risk", e.target.value)}
          />
          <span>—</span>
          <input
            type="number"
            min="0"
            max="1"
            step=".01"
            aria-label="Maximum risk score"
            placeholder="Max"
            value={filters.max_risk}
            onChange={(e) => set("max_risk", e.target.value)}
          />
        </div>
        <div className="filter-group-label">AMOUNT · SOURCE UNITS</div>
        <div className="range-fields">
          <input
            type="number"
            min="0"
            aria-label="Minimum amount"
            placeholder="Min"
            value={filters.min_amount}
            onChange={(e) => set("min_amount", e.target.value)}
          />
          <span>—</span>
          <input
            type="number"
            min="0"
            aria-label="Maximum amount"
            placeholder="Max"
            value={filters.max_amount}
            onChange={(e) => set("max_amount", e.target.value)}
          />
        </div>
        <div className="filter-group-label">DATASET TIME · SECONDS</div>
        <div className="range-fields">
          <input
            type="number"
            min="0"
            aria-label="Minimum dataset time"
            placeholder="From"
            value={filters.min_time}
            onChange={(e) => set("min_time", e.target.value)}
          />
          <span>—</span>
          <input
            type="number"
            min="0"
            aria-label="Maximum dataset time"
            placeholder="To"
            value={filters.max_time}
            onChange={(e) => set("max_time", e.target.value)}
          />
        </div>
        <label className="field">
          Observed label
          <select
            aria-label="Observed label filter"
            value={filters.label}
            onChange={(e) => set("label", e.target.value)}
          >
            <option value="all">All / unlabeled</option>
            <option value="1">Observed fraud</option>
            <option value="0">Observed legitimate</option>
          </select>
        </label>
        <div className="save-view">
          <input
            aria-label="Saved view name"
            placeholder="Name this query…"
            value={name}
            maxLength={100}
            onChange={(e) => setName(e.target.value)}
          />
          <button
            className="secondary full"
            disabled={!name.trim() || saving}
            onClick={save}
          >
            <Save size={13} />
            Save query configuration
          </button>
        </div>
        <p className="muted">
          Saved views are shared in this local research workspace. Scores are
          uncalibrated.
        </p>
      </aside>
      <Panel
        title="Transaction intelligence"
        meta={
          <a className="secondary" href={"/api/v1/transactions/export?" + key}>
            <ArrowDownToLine size={13} />
            Export filtered CSV
          </a>
        }
      >
        <div className="toolbar">
          <label className="search-input">
            <Search size={14} />
            <input
              aria-label="Search transactions"
              placeholder="Transaction ID or dataset name…"
              value={filters.q}
              onChange={(e) => set("q", e.target.value)}
            />
          </label>
          <select
            aria-label="Sort transactions"
            value={filters.sort}
            onChange={(e) => set("sort", e.target.value)}
          >
            <option value="risk_score">Risk score</option>
            <option value="amount">Amount</option>
            <option value="time">Dataset time</option>
            <option value="id">Transaction ID</option>
          </select>
          <button
            className="secondary"
            aria-label="Reverse sort direction"
            onClick={() =>
              set("direction", filters.direction === "asc" ? "desc" : "asc")
            }
          >
            {filters.direction === "asc" ? "Ascending ↑" : "Descending ↓"}
          </button>
        </div>
        <div className="query-summary">
          <span className="mono">
            {data?.total.toLocaleString() ?? "…"} MATCHING RECORDS
          </span>
          {active.map(([k, v]) => (
            <button
              key={k}
              onClick={() =>
                set(k as keyof Filters, defaults[k as keyof Filters])
              }
            >
              {k.replaceAll("_", " ")}: {v} ×
            </button>
          ))}
        </div>
        {data ? (
          <>
            <TxTable items={data.items} onSelect={onSelect} />
            <div className="pagination">
              <span>
                Page {page} / {Math.max(1, Math.ceil(data.total / 20))}
              </span>
              <div>
                <button
                  className="secondary"
                  disabled={page === 1}
                  onClick={() => setPage((p) => p - 1)}
                >
                  <ChevronLeft size={13} />
                  Previous
                </button>
                <button
                  className="secondary"
                  disabled={page * 20 >= data.total}
                  onClick={() => setPage((p) => p + 1)}
                >
                  Next
                  <ChevronRight size={13} />
                </button>
              </div>
            </div>
          </>
        ) : (
          <Loading />
        )}
      </Panel>
    </div>
  );
}
