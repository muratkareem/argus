import { CopilotWorkspace } from "./pages/CopilotWorkspace";
import { GraphIntelligence } from "./pages/GraphIntelligence";
import { InvestigationWorkspace } from "./pages/InvestigationWorkspace";
import { TransactionIntelligence } from "./pages/TransactionIntelligence";
import { Risk, Empty, Panel, Metric, TxTable, Loading } from "./ui";
import { CommandMenu } from "./components/CommandMenu";
export { Risk, Empty } from "./ui";
import { useEffect, useState } from "react";
import {
  Activity,
  ArrowDownToLine,
  ArrowRight,
  Check,
  ChevronRight,
  CircleHelp,
  Database,
  FileSearch,
  FlaskConical,
  Focus,
  LayoutDashboard,
  LoaderCircle,
  Network,
  Plus,
  Search,
  Settings as SettingsIcon,
  ShieldCheck,
  Sparkles,
  Upload,
  X,
} from "lucide-react";
import {
  Area,
  AreaChart,
  Bar,
  BarChart,
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { api, amount, download, percent, send } from "./api";
import type {
  Case,
  Dataset,
  Experiment,
  Models,
  Overview,
  Settings,
  Tx,
} from "./types";

const pages = [
  ["overview", "Overview", LayoutDashboard],
  ["transactions", "Transactions", Activity],
  ["detection", "Fraud Detection", ShieldCheck],
  ["laboratory", "ML Laboratory", FlaskConical],
  ["investigations", "Investigations", FileSearch],
  ["graph", "Intelligence Graph", Network],
  ["copilot", "AI Copilot", Sparkles],
  ["settings", "Settings", SettingsIcon],
] as const;
const route = () => location.hash.slice(1).split(/[/?]/)[0] || "overview";
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

export default function App() {
  const [page, setPage] = useState(route),
    [revision, setRevision] = useState(0),
    [error, setError] = useState(""),
    [notice, setNotice] = useState(""),
    [uploadOpen, setUploadOpen] = useState(false),
    [selectedTx, setSelectedTx] = useState<number | null>(null),
    [settings, setSettings] = useState<Settings | null>(null),
    [commandOpen, setCommandOpen] = useState(false),
    [density, setDensity] = useState(
      () => localStorage.getItem("argus-density") || "compact",
    );
  useEffect(() => {
    const change = () => setPage(route());
    addEventListener("hashchange", change);
    return () => removeEventListener("hashchange", change);
  }, []);
  useEffect(() => {
    api<Settings>("/settings")
      .then(setSettings)
      .catch((e) => setError(e.message));
  }, []);
  useEffect(() => {
    if (notice) {
      const id = setTimeout(() => setNotice(""), 7000);
      return () => clearTimeout(id);
    }
  }, [notice]);
  useEffect(() => {
    const shortcut = (event: KeyboardEvent) => {
      if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === "k") {
        event.preventDefault();
        setSelectedTx(null);
        setUploadOpen(false);
        setCommandOpen((open) => !open);
      }
      if (event.key === "Escape") {
        setCommandOpen(false);
        setSelectedTx(null);
        setUploadOpen(false);
      }
    };
    addEventListener("keydown", shortcut);
    return () => removeEventListener("keydown", shortcut);
  }, []);
  useEffect(() => {
    if (!commandOpen && !uploadOpen && selectedTx == null) return;
    const dialog = [
      ...document.querySelectorAll<HTMLElement>('[role="dialog"]'),
    ].at(-1);
    if (!dialog) return;
    const previous = document.activeElement as HTMLElement;
    const controls = () =>
      [
        ...dialog.querySelectorAll<HTMLElement>(
          'button:not(:disabled),a[href],input:not(:disabled),select:not(:disabled),textarea:not(:disabled),[tabindex="0"]',
        ),
      ].filter((el) => el.getClientRects().length > 0);
    if (!dialog.contains(document.activeElement)) controls()[0]?.focus();
    const trap = (event: KeyboardEvent) => {
      if (event.key !== "Tab") return;
      const nodes = controls(),
        first = nodes[0],
        last = nodes.at(-1);
      if (event.shiftKey && document.activeElement === first) {
        event.preventDefault();
        last?.focus();
      } else if (!event.shiftKey && document.activeElement === last) {
        event.preventDefault();
        first?.focus();
      }
    };
    document.addEventListener("keydown", trap);
    return () => {
      document.removeEventListener("keydown", trap);
      if (previous?.isConnected) previous.focus();
    };
  }, [commandOpen, uploadOpen, selectedTx]);
  const refresh = () => setRevision((n) => n + 1);
  const fail = (e: unknown) =>
    setError(e instanceof Error ? e.message : String(e));
  const current = pages.find((p) => p[0] === page) ?? pages[0];
  return (
    <div className="app-shell" data-density={density}>
      <aside className="sidebar">
        <a className="brand" href="#overview" aria-label="ARGUS overview">
          <div className="brand-mark">
            <Focus size={27} />
          </div>
          <span>
            ARGUS<small>FINANCIAL INTELLIGENCE</small>
          </span>
        </a>
        <div className="workspace-label">
          <span className="workspace-icon">A</span>
          <div>
            Research workspace<small>Local environment</small>
          </div>
          <span className="workspace-version">v0.1</span>
        </div>
        <div className="nav-label">WORKSPACE</div>
        <nav>
          {pages.slice(0, 7).map(([id, label, Icon]) => (
            <a key={id} href={"#" + id} className={page === id ? "active" : ""}>
              <Icon size={17} />
              {label}
              {id === "copilot" && <span className="nav-tag">LOCAL</span>}
            </a>
          ))}
        </nav>
        <div className="sidebar-bottom">
          <a href="#settings" className={page === "settings" ? "active" : ""}>
            <SettingsIcon size={17} />
            Settings
          </a>
          <div className="research-card">
            <ShieldCheck size={17} />
            <span>
              Built for research<small>Experimental · local use</small>
            </span>
          </div>
          <div className="analyst">
            <div className="avatar">RA</div>
            <span>
              Research analyst<small>ARGUS workspace</small>
            </span>
            <span className="online-dot" />
          </div>
        </div>
      </aside>
      <div className="main-shell">
        <header className="topbar">
          <div className="breadcrumb">
            Workspace <ChevronRight size={13} />
            <span>{current[1]}</span>
          </div>
          <button
            className="global-search-trigger"
            onClick={() => setCommandOpen(true)}
          >
            <Search size={14} />
            <span>Search workspace</span>
            <kbd>⌘ K</kbd>
          </button>
          <div className="topbar-right">
            <label className="density-control">
              <span>Density</span>
              <select
                aria-label="Display density"
                value={density}
                onChange={(e) => {
                  setDensity(e.target.value);
                  localStorage.setItem("argus-density", e.target.value);
                }}
              >
                <option value="compact">Compact</option>
                <option value="comfortable">Comfortable</option>
              </select>
            </label>
            <span className="environment">
              <span className="online-dot" />
              LOCAL RESEARCH
            </span>
            <a
              className="help"
              href="http://127.0.0.1:8000/docs"
              target="_blank"
              rel="noreferrer"
              title="Open API documentation"
            >
              <CircleHelp size={17} />
            </a>
            <div className="avatar small">RA</div>
          </div>
        </header>
        <main>
          <div className="page-title">
            <div>
              <div className="eyebrow">ARGUS / ANALYST WORKSPACE</div>
              <h1>
                {current[1] === "Overview" ? "Command Center" : current[1]}
              </h1>
              <p>
                {
                  (
                    {
                      overview:
                        "A clear view of transaction risk. A focused path to investigation.",
                      transactions:
                        "Explore stored transactions, inspect model scores, and follow the evidence.",
                      detection:
                        "Import transaction data and apply the active fraud detection model.",
                      laboratory:
                        "Reproducible experiments. Untouched test sets. Measured performance.",
                      investigations:
                        "Turn flagged transactions into documented analyst decisions.",
                      graph:
                        "Explore connections in an explicitly synthetic relationship network.",
                      copilot:
                        "Local assistance grounded in selected records and analyst evidence.",
                      settings:
                        "Runtime configuration and research environment.",
                    } as Record<string, string>
                  )[page]
                }
              </p>
            </div>
            <button className="primary" onClick={() => setUploadOpen(true)}>
              <Upload size={15} />
              Import dataset
            </button>
          </div>
          {error && (
            <div role="alert" className="alert error">
              {error}
              <button aria-label="Dismiss error" onClick={() => setError("")}>
                <X size={15} />
              </button>
            </div>
          )}
          {notice && (
            <div role="status" className="alert good">
              <Check size={15} />
              {notice}
              <button
                aria-label="Dismiss notification"
                onClick={() => setNotice("")}
              >
                <X size={15} />
              </button>
            </div>
          )}
          <div className="provenance-banner">
            <div className="banner-icon">
              <FlaskConical size={17} />
            </div>
            <span>
              <b>Research environment</b>
              <span className="banner-separator">/</span>Synthetic fixtures and
              ULB imports are tracked separately. Scores are uncalibrated.
            </span>
            <span className="banner-tag">EXPERIMENTAL</span>
          </div>
          {page === "overview" && (
            <OverviewPage
              revision={revision}
              onSelect={setSelectedTx}
              fail={fail}
            />
          )}
          {page === "transactions" && (
            <TransactionIntelligence
              revision={revision}
              onSelect={setSelectedTx}
              fail={fail}
            />
          )}
          {page === "detection" && (
            <Detection
              revision={revision}
              refresh={refresh}
              upload={() => setUploadOpen(true)}
              notify={setNotice}
              fail={fail}
            />
          )}
          {page === "laboratory" && (
            <Laboratory revision={revision} fail={fail} />
          )}
          {page === "investigations" && (
            <InvestigationWorkspace
              revision={revision}
              onSelect={setSelectedTx}
              fail={fail}
              notify={setNotice}
            />
          )}
          {page === "graph" && (
            <GraphIntelligence fail={fail} notify={setNotice} />
          )}
          {page === "copilot" && (
            <CopilotWorkspace
              settings={settings}
              fail={fail}
              notify={setNotice}
              onSelect={setSelectedTx}
            />
          )}
          {page === "settings" && <SettingsPage settings={settings} />}
          {!pages.some((p) => p[0] === page) && (
            <Empty>
              Unknown page. <a href="#overview">Return to overview</a>.
            </Empty>
          )}
          <footer>
            <span>
              <Focus size={12} />
              ARGUS Intelligence Platform
            </span>
            <span>
              Research prototype <i /> No real financial system connections
            </span>
          </footer>
        </main>
      </div>
      {commandOpen && (
        <CommandMenu
          pages={pages.map(([id, label]) => ({ id, label }))}
          close={() => setCommandOpen(false)}
          onTransaction={setSelectedTx}
        />
      )}
      {uploadOpen && (
        <UploadModal
          close={() => setUploadOpen(false)}
          done={(message) => {
            setNotice(message);
            setUploadOpen(false);
            refresh();
          }}
          fail={fail}
          maxUploadMiB={settings?.max_upload_mib ?? 192}
        />
      )}
      {selectedTx != null && (
        <TransactionDrawer
          id={selectedTx}
          close={() => setSelectedTx(null)}
          fail={fail}
          notify={setNotice}
          refresh={refresh}
        />
      )}
    </div>
  );
}

function OverviewPage({
  revision,
  onSelect,
  fail,
}: {
  revision: number;
  onSelect: (id: number) => void;
  fail: (e: unknown) => void;
}) {
  const [data, setData] = useState<Overview | null>(null),
    [experiment, setExperiment] = useState<Experiment | null>(null),
    [recentCases, setRecentCases] = useState<Case[]>([]),
    [riskBand, setRiskBand] = useState(9);
  useEffect(() => {
    api<Overview>("/overview").then(setData).catch(fail);
    api<Case[]>("/cases").then(setRecentCases).catch(fail);
    api<Models>("/models")
      .then((d) =>
        setExperiment(
          d.experiments.find((e) => e.version === d.active_version) ?? null,
        ),
      )
      .catch(fail);
  }, [revision]);
  if (!data) return <Loading />;
  const model = experiment?.models.find(
    (m) => m.name === experiment.selected_model,
  );
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
          label="TRANSACTION VOLUME"
          value={
            <>
              <span className="metric-unit">∑</span>
              <span className="volume-full">{amount(data.volume)}</span>
              <span
                className="volume-compact"
                title={amount(data.volume)}
                aria-label={amount(data.volume)}
              >
                {new Intl.NumberFormat("en-US", {
                  notation: "compact",
                  maximumFractionDigits: 2,
                }).format(data.volume)}
              </span>
            </>
          }
          detail={<>Amount units · source denomination unspecified</>}
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
              <span className="online-dot" />
              {model ? "ACTIVE" : "UNTRAINED"}
            </span>
          }
        >
          {model && experiment ? (
            <div className="model-card">
              <div className="model-icon">
                <FlaskConical size={24} />
              </div>
              <h3>{model.name}</h3>
              <p>Selected by validation average precision</p>
              <div className="model-source">
                {experiment.provenance.toUpperCase()} TRAINING DATA
              </div>
              <div className="model-stat">
                <span>Test precision</span>
                <b>{percent(model.test.precision)}</b>
              </div>
              <div className="model-stat">
                <span>Test recall</span>
                <b>{percent(model.test.recall)}</b>
              </div>
              <div className="model-stat">
                <span>Test PR-AUC / AP</span>
                <b className="teal">
                  {model.test.average_precision.toFixed(3)}
                </b>
              </div>
              <button
                className="secondary full"
                onClick={() => nav("laboratory")}
              >
                Open ML Laboratory <ArrowRight size={13} />
              </button>
              <small>
                {experiment.provenance === "synthetic"
                  ? "Synthetic results do not establish ULB performance."
                  : "Held-out ULB test metrics. Live-system generalization is unverified."}
              </small>
            </div>
          ) : (
            <Empty>Train a model using the README instructions.</Empty>
          )}
        </Panel>
      </div>
      <Panel
        title="Recent investigations"
        meta={
          <button className="text-button" onClick={() => nav("investigations")}>
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
      <div className="insight-bar">
        <ShieldCheck size={19} />
        <span>
          <b>
            Labeled-data detection rate: {percent(data.fraud_detection_rate)}
          </b>
          <small>
            Computed over {data.labeled_scored_fraud} labeled fraud records with
            stored scores. This is an operational view, separate from held-out
            test evaluation.
          </small>
        </span>
      </div>
    </>
  );
}

function UploadModal({
  close,
  done,
  fail,
  maxUploadMiB,
}: {
  close: () => void;
  done: (s: string) => void;
  fail: (e: unknown) => void;
  maxUploadMiB: number;
}) {
  const [file, setFile] = useState<File | null>(null),
    [source, setSource] = useState("synthetic"),
    [busy, setBusy] = useState(false),
    [localError, setLocalError] = useState("");
  async function upload() {
    if (!file) return;
    setBusy(true);
    setLocalError("");
    const body = new FormData();
    body.append("file", file);
    body.append("provenance", source);
    try {
      const result = await api<{
        imported: number;
        duplicates: number;
        model_note: string;
      }>("/datasets/upload", { method: "POST", body });
      done(
        `Imported ${result.imported} transactions; ${result.duplicates} duplicates skipped. ${result.model_note}`,
      );
    } catch (e) {
      setLocalError((e as Error).message);
      fail(e);
    } finally {
      setBusy(false);
    }
  }
  return (
    <div className="overlay" onClick={close}>
      <section
        className="modal"
        role="dialog"
        aria-modal="true"
        aria-labelledby="upload-title"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="panel-head">
          <h2 id="upload-title">Import transaction dataset</h2>
          <button
            className="icon-button"
            onClick={close}
            aria-label="Close import"
          >
            <X size={18} />
          </button>
        </div>
        <div className="modal-body">
          <p>
            CSV schema: Time, V1–V28, Amount, and optional Class. Maximum{" "}
            {maxUploadMiB} MiB. Uploaded data stays in your configured database.
          </p>
          <label className="field">
            Data provenance
            <select value={source} onChange={(e) => setSource(e.target.value)}>
              <option value="synthetic">Synthetic demonstration data</option>
              <option value="ulb">ULB benchmark data</option>
            </select>
          </label>
          <label className="dropzone">
            <Upload size={28} />
            <strong>{file?.name ?? "Choose a CSV file"}</strong>
            <span>Schema validation and duplicate detection included</span>
            <input
              type="file"
              accept=".csv"
              aria-label="CSV file"
              onChange={(e) => setFile(e.target.files?.[0] ?? null)}
            />
          </label>
          <p className="muted">
            Imports are scored only when the active model has matching
            provenance. Train on your authorized ULB copy before scoring ULB
            data.
          </p>
          {localError && (
            <div role="alert" className="error-text">
              {localError}
            </div>
          )}
          <button
            className="primary full"
            disabled={!file || busy}
            onClick={upload}
          >
            {busy ? (
              <LoaderCircle className="spin" size={15} />
            ) : (
              <Upload size={15} />
            )}{" "}
            {busy ? "Validating and importing…" : "Import transactions"}
          </button>
        </div>
      </section>
    </div>
  );
}

function TransactionDrawer({
  id,
  close,
  fail,
  notify,
  refresh,
}: {
  id: number;
  close: () => void;
  fail: (e: unknown) => void;
  notify: (s: string) => void;
  refresh: () => void;
}) {
  const [tx, setTx] = useState<Tx | null>(null),
    [explanation, setExplanation] = useState<{
      features: { feature: string; value: number; contribution: number }[];
      model_version: string;
      matches_stored_prediction: boolean;
      caveat: string;
    } | null>(null),
    [busy, setBusy] = useState(false),
    [cases, setCases] = useState<Case[]>([]),
    [linkId, setLinkId] = useState("");
  useEffect(() => {
    api<Tx>(`/transactions/${id}`).then(setTx).catch(fail);
    api<Case[]>("/cases").then(setCases).catch(fail);
  }, [id]);
  async function explain() {
    setBusy(true);
    try {
      setExplanation(await api(`/transactions/${id}/explanation`));
    } catch (e) {
      fail(e);
    } finally {
      setBusy(false);
    }
  }
  async function create() {
    try {
      const c = await api<Case>(
        "/cases",
        send("POST", {
          title: `Review TX-${String(id).padStart(6, "0")}`,
          priority: "High",
          transaction_ids: [id],
        }),
      );
      notify(`Investigation #${c.id} created and linked.`);
      refresh();
      close();
      nav("investigations/" + c.id);
    } catch (e) {
      fail(e);
    }
  }
  async function link() {
    if (!linkId) return;
    try {
      await api(
        `/cases/${linkId}/transactions`,
        send("POST", { transaction_id: id }),
      );
      notify(`Transaction linked to investigation #${linkId}.`);
      setTx({
        ...tx!,
        case_ids: [...new Set([...(tx?.case_ids ?? []), Number(linkId)])],
      });
      refresh();
    } catch (e) {
      fail(e);
    }
  }
  return (
    <div className="overlay drawer-overlay" onClick={close}>
      <section
        className="drawer"
        role="dialog"
        aria-modal="true"
        aria-label="Transaction details"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="panel-head">
          <h2 className="mono">TX-{String(id).padStart(6, "0")}</h2>
          <button
            className="icon-button"
            aria-label="Close transaction"
            onClick={close}
          >
            <X size={18} />
          </button>
        </div>
        {tx ? (
          <div className="drawer-body">
            <div className="detail-heading">
              <Risk tx={tx} />
              <span className="mini-tag">{tx.provenance.toUpperCase()}</span>
            </div>
            <div className="detail-score">
              <span>MODEL RISK SCORE</span>
              <strong>{percent(tx.risk_score)}</strong>
              <small>Uncalibrated · threshold {percent(tx.threshold)}</small>
            </div>
            <div className="detail-row">
              <span>Amount (unspecified units)</span>
              <b className="mono">{amount(tx.amount)}</b>
            </div>
            <div className="detail-row">
              <span>Dataset time</span>
              <b>{tx.time.toFixed(1)} seconds</b>
            </div>
            <div className="detail-row">
              <span>Observed label</span>
              <b>
                {tx.label == null
                  ? "Unlabeled"
                  : tx.label === 1
                    ? "Fraud"
                    : "Legitimate"}
              </b>
            </div>
            <div className="detail-row">
              <span>Model version</span>
              <code>{tx.model_version ?? "Unscored"}</code>
            </div>
            <h3>Investigation</h3>
            <div className="case-links">
              {tx.case_ids?.map((c) => (
                <button
                  className="text-button"
                  key={c}
                  onClick={() => {
                    close();
                    nav("investigations/" + c);
                  }}
                >
                  Case #{c} <ArrowRight size={12} />
                </button>
              ))}
            </div>
            <button className="primary full" onClick={create}>
              <Plus size={15} />
              Create linked investigation
            </button>
            {cases.length > 0 && (
              <div className="inline-form">
                <select
                  aria-label="Existing investigation"
                  value={linkId}
                  onChange={(e) => setLinkId(e.target.value)}
                >
                  <option value="">Link to existing case…</option>
                  {cases.map((c) => (
                    <option key={c.id} value={c.id}>
                      #{c.id} {c.title}
                    </option>
                  ))}
                </select>
                <button className="secondary" disabled={!linkId} onClick={link}>
                  Link
                </button>
              </div>
            )}
            <h3>Prediction explanation</h3>
            <p className="muted">
              SHAP contributions describe the model’s use of anonymized
              features. They cannot establish why a real transaction is
              fraudulent.
            </p>
            <button
              className="secondary full"
              disabled={busy}
              onClick={explain}
            >
              {busy ? (
                <LoaderCircle size={15} className="spin" />
              ) : (
                <FlaskConical size={15} />
              )}
              Compute SHAP explanation
            </button>
            {explanation && (
              <div className="explanation">
                {!explanation.matches_stored_prediction && (
                  <p className="error-text">
                    Active model differs from stored score. This explanation
                    uses {explanation.model_version}.
                  </p>
                )}
                <p className="muted">
                  Top contributions · positive values increase model output
                </p>
                {explanation.features.slice(0, 8).map((f) => (
                  <div className="shap-row" key={f.feature}>
                    <span className="mono">{f.feature}</span>
                    <div>
                      <i
                        className={f.contribution > 0 ? "positive" : "negative"}
                        style={{
                          width: `${Math.min(Math.abs(f.contribution) * 22, 100)}%`,
                        }}
                      />
                    </div>
                    <b className="mono">
                      {f.contribution > 0 ? "+" : ""}
                      {f.contribution.toFixed(3)}
                    </b>
                  </div>
                ))}
              </div>
            )}
            <details>
              <summary>All 30 model features</summary>
              <div className="feature-grid">
                {Object.entries(tx.features ?? {}).map(([k, v]) => (
                  <div key={k}>
                    <span>{k}</span>
                    <code>{v.toFixed(4)}</code>
                  </div>
                ))}
              </div>
            </details>
          </div>
        ) : (
          <Loading />
        )}
      </section>
    </div>
  );
}

function Detection({
  revision,
  refresh,
  upload,
  notify,
  fail,
}: {
  revision: number;
  refresh: () => void;
  upload: () => void;
  notify: (s: string) => void;
  fail: (e: unknown) => void;
}) {
  const [datasets, setDatasets] = useState<Dataset[]>([]),
    [models, setModels] = useState<Models | null>(null),
    [busy, setBusy] = useState<number | null>(null);
  useEffect(() => {
    api<Dataset[]>("/datasets").then(setDatasets).catch(fail);
    api<Models>("/models").then(setModels).catch(fail);
  }, [revision]);
  async function score(id: number) {
    setBusy(id);
    try {
      const r = await api<{ scored: number }>(`/datasets/${id}/score`, {
        method: "POST",
      });
      notify(`Scored ${r.scored} transactions using the active model.`);
      refresh();
    } catch (e) {
      fail(e);
    } finally {
      setBusy(null);
    }
  }
  return (
    <>
      <div className="two-grid">
        <Panel title="Inference pipeline">
          <div className="pipeline-steps">
            {[
              [
                "01",
                "Validate schema",
                "Time, V1–V28, Amount · optional Class",
              ],
              [
                "02",
                "Resolve provenance",
                "ULB and synthetic models stay separate",
              ],
              ["03", "Score transactions", "Actual serialized model inference"],
              [
                "04",
                "Persist evidence",
                "Score, threshold, model version, source",
              ],
            ].map(([n, title, desc]) => (
              <div key={n}>
                <span className="step-number">{n}</span>
                <div>
                  <h3>{title}</h3>
                  <p>{desc}</p>
                </div>
                <Check size={16} />
              </div>
            ))}
          </div>
        </Panel>
        <Panel title="Active model">
          <div className="padded">
            <p className="muted">Current model version</p>
            <code className="wrap-code">
              {models?.active_version ?? "No model trained"}
            </code>
            <p>
              Train reproducibly from the command line. A new experiment
              activates only after its artifacts have been written.
            </p>
            <pre>
              PYTHONPATH=backend uv run python -m app.ml
              <br /> --csv data/private/creditcard.csv
            </pre>
            <button className="secondary" onClick={() => nav("laboratory")}>
              Inspect experiments
              <ArrowRight size={14} />
            </button>
          </div>
        </Panel>
      </div>
      <Panel
        title="Imported datasets"
        meta={
          <button className="secondary" onClick={upload}>
            <Plus size={14} />
            Import CSV
          </button>
        }
      >
        {datasets.length ? (
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Dataset</th>
                  <th>Source</th>
                  <th>Stored rows</th>
                  <th>Duplicates</th>
                  <th>Batch inference</th>
                </tr>
              </thead>
              <tbody>
                {datasets.map((d) => (
                  <tr key={d.id}>
                    <td>
                      {d.name}
                      <small className="table-sub">
                        {new Date(d.created_at).toLocaleString()}
                      </small>
                    </td>
                    <td>
                      <span className="badge neutral">{d.provenance}</span>
                    </td>
                    <td className="mono">{d.rows}</td>
                    <td className="mono">{d.duplicates}</td>
                    <td>
                      <button
                        className="secondary"
                        disabled={busy !== null || d.rows === 0}
                        onClick={() => score(d.id)}
                      >
                        {busy === d.id ? (
                          <LoaderCircle size={14} className="spin" />
                        ) : (
                          <ShieldCheck size={14} />
                        )}
                        Score dataset
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <Empty>No datasets imported yet.</Empty>
        )}
      </Panel>
    </>
  );
}

function Laboratory({
  revision,
  fail,
}: {
  revision: number;
  fail: (e: unknown) => void;
}) {
  const [models, setModels] = useState<Models | null>(null),
    [version, setVersion] = useState(""),
    [selected, setSelected] = useState("");
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
          <div className="confusion">
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
              impurity / split importance for tree models. These scales are not
              comparable across algorithms.
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
              Preprocessing is fitted on training data. Candidate parameters and
              decision thresholds are selected using validation data. Algorithm
              selection precedes test evaluation.
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
    </>
  );
}

function SettingsPage({ settings }: { settings: Settings | null }) {
  return settings ? (
    <div className="two-grid">
      <Panel title="Environment">
        <div className="padded">
          {[
            ["Database", settings.database],
            ["Authentication", settings.authentication],
            ["Upload limit", `${settings.max_upload_mib} MiB`],
            ["Ollama", settings.ollama_enabled ? "Enabled" : "Disabled"],
            ["Local model", settings.ollama_model],
          ].map(([k, v]) => (
            <div className="detail-row" key={k}>
              <span>{k}</span>
              <b>{v}</b>
            </div>
          ))}
          <p className="muted">
            Configuration comes from environment variables or a local .env file.
            Restart the backend after changing configuration.
          </p>
        </div>
      </Panel>
      <Panel title="Research boundaries">
        <div className="padded">
          <h3>Educational prototype</h3>
          <p>
            No authentication, bank integrations, or compliance certification.
            Keep the application on your own computer or a trusted private
            network.
          </p>
          <p>
            ULB uses anonymized features. Synthetic data contains artificial
            patterns and is never presented as benchmark evidence.
          </p>
          <p>
            Model scores are uncalibrated. An alert is a request for analyst
            review, not proof of fraud.
          </p>
          <a
            className="secondary"
            href="http://127.0.0.1:8000/docs"
            target="_blank"
            rel="noreferrer"
          >
            Open API documentation <ArrowRight size={14} />
          </a>
        </div>
      </Panel>
    </div>
  ) : (
    <Loading />
  );
}
