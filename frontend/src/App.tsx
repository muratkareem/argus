import { ExplanationContributions } from "./components/ExplanationContributions";
import { Risk, Empty, Loading } from "./ui";
import { CommandMenu } from "./components/CommandMenu";
export { Risk, Empty } from "./ui";
import { lazy, Suspense, useEffect, useState } from "react";
import {
  Activity,
  ArrowRight,
  Check,
  ChevronRight,
  CircleHelp,
  Menu,
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
  Upload,
  X,
} from "lucide-react";
import { api, send, percent, amount } from "./api";
import type { Case, Settings, Tx } from "./types";
const OverviewPage = lazy(() => import("./pages/OverviewPage"));
const Detection = lazy(() => import("./pages/Detection"));
const Laboratory = lazy(() => import("./pages/Laboratory"));
const TransactionIntelligence = lazy(() =>
  import("./pages/TransactionIntelligence").then((m) => ({
    default: m.TransactionIntelligence,
  })),
);
const InvestigationWorkspace = lazy(() =>
  import("./pages/InvestigationWorkspace").then((m) => ({
    default: m.InvestigationWorkspace,
  })),
);
const SystemInformation = lazy(() =>
  import("./pages/SystemInformation").then((m) => ({
    default: m.SystemInformation,
  })),
);
const GraphIntelligence = lazy(() =>
  import("./pages/GraphIntelligence").then((module) => ({
    default: module.GraphIntelligence,
  })),
);

const pages = [
  ["overview", "Overview", LayoutDashboard],
  ["transactions", "Transactions", Activity],
  ["detection", "Fraud Detection", ShieldCheck],
  ["laboratory", "Model performance", FlaskConical],
  ["investigations", "Investigations", FileSearch],
  ["graph", "Relationship demo", Network],
  ["settings", "Settings", SettingsIcon],
] as const;
const route = () => location.hash.slice(1).split(/[/?]/)[0] || "overview";
const nav = (page: string) => {
  location.hash = page;
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
    [navOpen, setNavOpen] = useState(false),
    [density, setDensity] = useState(
      () => localStorage.getItem("argus-density") || "compact",
    );
  useEffect(() => {
    const change = () => {
      setPage(route());
      setNavOpen(false);
      setSelectedTx(null);
      setUploadOpen(false);
      setCommandOpen(false);
      window.scrollTo(0, 0);
    };
    addEventListener("hashchange", change);
    return () => removeEventListener("hashchange", change);
  }, []);
  useEffect(() => {
    api<Settings>("/settings")
      .then(setSettings)
      .catch((e) => setError(e.message));
  }, [revision]);
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
        setNavOpen(false);
        setCommandOpen(false);
        setSelectedTx(null);
        setUploadOpen(false);
      }
    };
    addEventListener("keydown", shortcut);
    return () => removeEventListener("keydown", shortcut);
  }, []);
  useEffect(() => {
    if (!navOpen && !commandOpen && !uploadOpen && selectedTx == null) return;
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
  }, [navOpen, commandOpen, uploadOpen, selectedTx]);
  const refresh = () => setRevision((n) => n + 1);
  const fail = (e: unknown) =>
    setError(e instanceof Error ? e.message : String(e));
  const current = pages.find((p) => p[0] === page) ?? pages[0];
  return (
    <div
      className={"app-shell" + (navOpen ? " mobile-nav-open" : "")}
      data-density={density}
    >
      <a
        className="skip-link"
        href="#workspace-content"
        onClick={(event) => {
          event.preventDefault();
          document.getElementById("workspace-content")?.focus();
        }}
      >
        Skip to content
      </a>
      {navOpen && (
        <button
          className="nav-backdrop"
          aria-label="Close navigation"
          onClick={() => setNavOpen(false)}
        />
      )}
      <aside
        className="sidebar"
        id="workspace-navigation"
        aria-label="Workspace navigation"
        role={navOpen ? "dialog" : undefined}
        aria-modal={navOpen || undefined}
      >
        <a className="brand" href="#overview" aria-label="ARGUS overview">
          <div className="brand-mark">
            <Focus size={27} />
          </div>
          <span>
            ARGUS<small>FINANCIAL INTELLIGENCE</small>
          </span>
        </a>
        <div className="nav-label">REVIEW</div>
        <nav aria-label="Main workflow">
          {pages
            .filter(([id]) =>
              [
                "overview",
                "transactions",
                "detection",
                "investigations",
              ].includes(id),
            )
            .map(([id, label, Icon]) => (
              <a
                key={id}
                href={"#" + id}
                aria-current={page === id ? "page" : undefined}
                className={page === id ? "active" : ""}
                title={label}
              >
                <Icon size={18} />
                <span>{label}</span>
              </a>
            ))}
        </nav>
        <div className="nav-label">RESEARCH</div>
        <nav aria-label="Research tools">
          {pages
            .filter(([id]) => ["laboratory", "graph"].includes(id))
            .map(([id, label, Icon]) => (
              <a
                key={id}
                href={"#" + id}
                aria-current={page === id ? "page" : undefined}
                className={page === id ? "active" : ""}
                title={label}
              >
                <Icon size={18} />
                <span>{label}</span>
              </a>
            ))}
        </nav>
        <div className="sidebar-bottom">
          <a href="#settings" className={page === "settings" ? "active" : ""}>
            <SettingsIcon size={17} />
            Settings
          </a>
          <p className="sidebar-caption">
            Credit card fraud research
            <br />
            Private workspace
          </p>
        </div>
      </aside>
      <div className="main-shell">
        <header className="topbar">
          <button
            className="icon-button mobile-menu"
            aria-label="Open navigation"
            aria-expanded={navOpen}
            aria-controls="workspace-navigation"
            onClick={() => setNavOpen((v) => !v)}
          >
            <Menu size={20} />
          </button>
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
            <span className="environment">RESEARCH WORKSPACE</span>
            <a
              className="help"
              href="/docs"
              target="_blank"
              rel="noreferrer"
              title="Open API documentation"
            >
              <CircleHelp size={17} />
            </a>
          </div>
        </header>
        <main id="workspace-content" tabIndex={-1}>
          <div className="page-title">
            <div>
              <div className="eyebrow">FRAUD DETECTION WORKSPACE</div>
              <h1>{current[1]}</h1>
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
                      settings:
                        "Runtime configuration and research environment.",
                    } as Record<string, string>
                  )[page]
                }
              </p>
            </div>
            {["overview", "transactions", "detection"].includes(page) && (
              <button className="primary" onClick={() => setUploadOpen(true)}>
                <Upload size={15} />
                Import dataset
              </button>
            )}
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
          <Suspense fallback={<Loading />}>
            {page === "overview" && (
              <OverviewPage
                revision={revision}
                activeModel={settings?.active_model}
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
              <Suspense fallback={<Loading />}>
                <GraphIntelligence fail={fail} notify={setNotice} />
              </Suspense>
            )}
            {page === "settings" && (
              <SystemInformation
                settings={settings}
                revision={revision}
                reconnect={() => {
                  setError("");
                  refresh();
                }}
              />
            )}
            {!pages.some((p) => p[0] === page) && (
              <Empty>
                Unknown page. <a href="#overview">Return to overview</a>.
              </Empty>
            )}
          </Suspense>
          <footer>
            <span>
              <Focus size={12} />
              ARGUS Intelligence Platform
            </span>
            <span>
              Research use · Uncalibrated estimates · No bank connection
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
      output_space?: string;
      base_value?: number;
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
            <a
              className="secondary full"
              href={`#detection?transaction=${tx.id}`}
            >
              Use for prediction <ArrowRight size={14} />
            </a>
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
                <ExplanationContributions
                  features={explanation.features}
                  outputSpace={explanation.output_space}
                  baseValue={explanation.base_value}
                  modelVersion={explanation.model_version}
                  caveat={explanation.caveat}
                />
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
