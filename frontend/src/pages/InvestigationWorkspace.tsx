import { useEffect, useRef, useState } from "react";
import {
  ArrowDownToLine,
  ArrowRight,
  FileSearch,
  Plus,
  Search,
  ShieldCheck,
  Network,
  FlaskConical,
} from "lucide-react";
import { api, download, percent, amount, send } from "../api";
import { Panel, Empty, Loading, Risk } from "../ui";
import { SplitPane } from "../components/SplitPane";
import type { Case, Tx } from "../types";
type Event = {
  id: string;
  kind: string;
  payload: Record<string, string | number>;
  created_at: string;
};
const selection = () => Number(location.hash.split("/")[1]) || null;
export function InvestigationWorkspace({
  revision,
  onSelect,
  fail,
  notify,
}: {
  revision: number;
  onSelect: (id: number) => void;
  fail: (e: unknown) => void;
  notify: (s: string) => void;
}) {
  const [cases, setCases] = useState<Case[]>([]),
    [q, setQ] = useState(""),
    [title, setTitle] = useState(""),
    [id, setId] = useState<number | null>(selection),
    [active, setActive] = useState<Case | null>(null),
    [events, setEvents] = useState<Event[]>([]),
    [note, setNote] = useState(""),
    [decision, setDecision] = useState(""),
    [selectedTx, setSelectedTx] = useState<number | null>(null),
    [entityId, setEntityId] = useState<string | null>(null),
    [tab, setTab] = useState("timeline"),
    [busy, setBusy] = useState(false);
  const loadToken = useRef(0);
  const load = async () => {
    try {
      setCases(await api<Case[]>("/cases?q=" + encodeURIComponent(q)));
    } catch (e) {
      fail(e);
    }
  };
  useEffect(() => {
    void load();
  }, [q, revision]);
  useEffect(() => {
    const changed = () => setId(selection());
    addEventListener("hashchange", changed);
    return () => removeEventListener("hashchange", changed);
  }, []);
  async function detail(caseId: number) {
    const token = ++loadToken.current;
    const [record, history] = await Promise.all([
      api<Case>(`/cases/${caseId}`),
      api<Event[]>(`/cases/${caseId}/timeline`),
    ]);
    if (selection() !== caseId || token !== loadToken.current) return;
    setActive(record);
    setEvents(history);
    setDecision(record.decision);
    setSelectedTx((previous) =>
      record.transaction_ids.includes(previous ?? -1)
        ? previous
        : (record.transaction_ids[0] ?? null),
    );
    setEntityId((previous) =>
      previous && record.entity_ids?.includes(previous)
        ? previous
        : record.transaction_ids.length
          ? null
          : (record.entity_ids?.[0] ?? null),
    );
  }
  useEffect(() => {
    if (id) detail(id).catch(fail);
    else setActive(null);
  }, [id, revision]);
  function select(caseId: number) {
    location.hash = `investigations/${caseId}`;
    setId(caseId);
  }
  async function create() {
    setBusy(true);
    try {
      const c = await api<Case>("/cases", send("POST", { title }));
      setTitle("");
      await load();
      select(c.id);
      notify(`Investigation #${c.id} created.`);
    } catch (e) {
      fail(e);
    } finally {
      setBusy(false);
    }
  }
  async function update(patch: Record<string, string>) {
    if (!id) return;
    setBusy(true);
    notify("");
    try {
      await api(`/cases/${id}`, send("PATCH", patch));
      await Promise.all([detail(id), load()]);
      notify("Investigation saved.");
    } catch (e) {
      fail(e);
    } finally {
      setBusy(false);
    }
  }
  async function addNote() {
    if (!id) return;
    setBusy(true);
    try {
      await api(`/cases/${id}/notes`, send("POST", { body: note }));
      setNote("");
      await detail(id);
    } catch (e) {
      fail(e);
    } finally {
      setBusy(false);
    }
  }
  const queue = (
    <Panel
      title="Investigation queue"
      meta={<span className="mono muted">{cases.length} cases</span>}
    >
      <div className="queue-controls">
        <label className="search-input">
          <Search size={13} />
          <input
            aria-label="Search investigations"
            placeholder="Search cases, notes, decisions…"
            value={q}
            onChange={(e) => setQ(e.target.value)}
          />
        </label>
        <div className="inline-form">
          <input
            aria-label="New investigation title"
            placeholder="New investigation title…"
            value={title}
            maxLength={200}
            onChange={(e) => setTitle(e.target.value)}
          />
          <button
            className="primary"
            aria-label="Create case"
            disabled={title.trim().length < 3 || busy}
            onClick={create}
          >
            <Plus size={14} />
          </button>
        </div>
      </div>
      <div className="case-queue">
        {cases.map((c) => (
          <button
            className={"case-queue-item " + (c.id === id ? "selected" : "")}
            key={c.id}
            aria-label={`#${c.id} · ${c.title}`}
            onClick={() => select(c.id)}
          >
            <div>
              <span className="mono">CASE-{String(c.id).padStart(4, "0")}</span>
              <span
                className={
                  "badge " +
                  (["Critical", "High"].includes(c.priority)
                    ? "danger"
                    : "neutral")
                }
              >
                {c.priority}
              </span>
            </div>
            <strong>
              #{c.id} · {c.title}
            </strong>
            <div>
              <span>{c.status}</span>
              <small>
                {c.transaction_ids.length} TX · {c.entity_ids?.length ?? 0}{" "}
                entities
              </small>
            </div>
          </button>
        ))}
        {!cases.length && (
          <Empty>
            No investigations yet. Create a case or link from a transaction.
          </Empty>
        )}
      </div>
    </Panel>
  );
  const center = active ? (
    <Panel
      title={`Investigation #${active.id} · ${active.title}`}
      meta={
        <button
          className="secondary"
          onClick={async () => {
            try {
              download(
                `argus-case-${active.id}.json`,
                await api(`/cases/${active.id}/export`),
              );
            } catch (e) {
              fail(e);
            }
          }}
        >
          <ArrowDownToLine size={13} />
          Export report
        </button>
      }
    >
      <div className="case-command-bar">
        <label className="field">
          Status
          <select
            disabled={busy}
            aria-label="Case status"
            value={active.status}
            onChange={(e) => update({ status: e.target.value })}
          >
            {[
              "Open",
              "In Review",
              "Escalated",
              "Resolved",
              "False Positive",
            ].map((s) => (
              <option key={s}>{s}</option>
            ))}
          </select>
        </label>
        <label className="field">
          Priority
          <select
            disabled={busy}
            aria-label="Case priority"
            value={active.priority}
            onChange={(e) => update({ priority: e.target.value })}
          >
            {["Low", "Medium", "High", "Critical"].map((s) => (
              <option key={s}>{s}</option>
            ))}
          </select>
        </label>
        <span className="muted mono">
          Created {new Date(active.created_at).toLocaleDateString()}
        </span>
      </div>
      <div className="workspace-tabs">
        <button
          className={tab === "timeline" ? "active" : ""}
          onClick={() => setTab("timeline")}
        >
          Timeline & evidence
        </button>
        <button
          className={tab === "decision" ? "active" : ""}
          onClick={() => setTab("decision")}
        >
          Analyst decision
        </button>
      </div>
      <div className="case-work-body">
        {tab === "timeline" ? (
          <>
            <div className="timeline">
              {events.map((event) => (
                <article
                  className={"timeline-event event-" + event.kind}
                  key={event.id}
                >
                  <span className="timeline-dot" />
                  <header>
                    <b>{event.kind.replaceAll("_", " ")}</b>
                    <time>{new Date(event.created_at).toLocaleString()}</time>
                  </header>
                  <p>
                    {event.kind === "created"
                      ? event.payload.title
                      : event.kind === "note"
                        ? event.payload.body
                        : event.kind.endsWith("_changed")
                          ? `${String(event.payload.before || "Empty")} → ${String(event.payload.after)}`
                          : event.payload.entity_id
                            ? `Synthetic entity ${event.payload.entity_id}`
                            : `Transaction #${event.payload.transaction_id}`}
                  </p>
                </article>
              ))}
            </div>
            <label className="field">
              Add an evidence note
              <textarea
                disabled={busy}
                aria-label="Investigation note"
                value={note}
                maxLength={10000}
                onChange={(e) => setNote(e.target.value)}
                placeholder="Record an observation and distinguish evidence from interpretation…"
              />
            </label>
            <button
              className="primary"
              disabled={!note.trim() || busy}
              onClick={addNote}
            >
              <Plus size={13} />
              Add note
            </button>
            <div className="decision-compact">
              <label className="field">
                Analyst decision
                <textarea
                  disabled={busy}
                  aria-label="Analyst decision"
                  value={decision}
                  maxLength={10000}
                  onChange={(e) => setDecision(e.target.value)}
                  placeholder="Assessment, uncertainty, and next steps…"
                />
              </label>
              <button
                className="secondary"
                disabled={busy}
                onClick={() => update({ decision })}
              >
                Save decision
              </button>
            </div>
          </>
        ) : (
          <>
            <label className="field">
              Analyst decision
              <textarea
                disabled={busy}
                aria-label="Analyst decision"
                value={decision}
                maxLength={10000}
                onChange={(e) => setDecision(e.target.value)}
                placeholder="Assessment, supporting evidence and uncertainty…"
              />
            </label>
            <button
              className="primary"
              disabled={busy}
              onClick={() => update({ decision })}
            >
              <ShieldCheck size={13} />
              Save decision
            </button>
            <p className="muted">
              Decisions are analyst opinions. Changes are appended to the case
              timeline.
            </p>
          </>
        )}
      </div>
    </Panel>
  ) : (
    <Panel title="Investigation workspace">
      <Empty>
        <FileSearch size={30} />
        Select a case to examine evidence, review its timeline, and record a
        decision.
      </Empty>
    </Panel>
  );
  const inspector = (
    <Panel
      title="Linked evidence"
      meta={<span className="mini-tag">CONTEXT</span>}
    >
      {active ? (
        <div className="evidence-inspector">
          <div className="filter-group-label">
            TRANSACTIONS · {active.transaction_ids.length}
          </div>
          <div className="evidence-links">
            {active.transaction_ids.map((txid) => (
              <button
                className={
                  "evidence-link " +
                  (selectedTx === txid && !entityId ? "active" : "")
                }
                key={txid}
                onClick={() => {
                  setSelectedTx(txid);
                  setEntityId(null);
                }}
              >
                <ShieldCheck size={12} />
                <span className="mono">TX-{String(txid).padStart(6, "0")}</span>
                <ArrowRight size={12} />
              </button>
            ))}
          </div>
          <div className="filter-group-label">
            SYNTHETIC GRAPH ENTITIES · {active.entity_ids?.length ?? 0}
          </div>
          <div className="evidence-links">
            {active.entity_ids?.map((e) => (
              <button
                className={"evidence-link " + (entityId === e ? "active" : "")}
                key={e}
                onClick={() => {
                  setEntityId(e);
                  setSelectedTx(null);
                }}
              >
                <Network size={12} />
                {e}
                <ArrowRight size={12} />
              </button>
            ))}
          </div>
          {entityId ? (
            <EntityEvidence id={entityId} fail={fail} />
          ) : selectedTx ? (
            <TransactionEvidence
              id={selectedTx}
              onSelect={onSelect}
              fail={fail}
            />
          ) : (
            <p className="muted">
              Link records from the transaction inspector or synthetic graph.
            </p>
          )}
          <button
            className="secondary full"
            onClick={() => {
              location.hash = `copilot/${active.id}`;
            }}
          >
            Summarize case with Copilot
            <ArrowRight size={12} />
          </button>
        </div>
      ) : (
        <Empty>Evidence follows the selected case.</Empty>
      )}
    </Panel>
  );
  return (
    <div className="investigation-workspace">
      <div className="workspace-context">
        <FileSearch size={14} />
        <span>INVESTIGATION WORKBENCH</span>
        <span className="muted">Queue → case timeline → linked evidence</span>
        <small>Drag dividers or use ← → when focused</small>
      </div>
      <SplitPane
        storageKey="argus-case-queue-width"
        initial={25}
        min={18}
        max={42}
        label="Resize investigation queue"
        first={queue}
        second={
          <SplitPane
            storageKey="argus-case-evidence-width"
            initial={64}
            min={45}
            max={78}
            label="Resize case and evidence panels"
            first={center}
            second={inspector}
          />
        }
      />
    </div>
  );
}
function TransactionEvidence({
  id,
  onSelect,
  fail,
}: {
  id: number;
  onSelect: (id: number) => void;
  fail: (e: unknown) => void;
}) {
  const [tx, setTx] = useState<Tx | null>(null),
    [explain, setExplain] = useState<{
      features: { feature: string; contribution: number }[];
      model_version: string;
      matches_stored_prediction: boolean;
    } | null>(null),
    [busy, setBusy] = useState(false);
  useEffect(() => {
    setTx(null);
    setExplain(null);
    api<Tx>(`/transactions/${id}`).then(setTx).catch(fail);
  }, [id]);
  async function explainRecord() {
    setBusy(true);
    try {
      setExplain(await api(`/transactions/${id}/explanation`));
    } catch (e) {
      fail(e);
    } finally {
      setBusy(false);
    }
  }
  return tx ? (
    <div className="context-record">
      <div className="detail-heading">
        <Risk tx={tx} />
        <span className="mini-tag">{tx.provenance}</span>
      </div>
      <h3 className="mono">TX-{String(tx.id).padStart(6, "0")}</h3>
      <div className="context-score">
        {percent(tx.risk_score)}
        <small>Uncalibrated model score</small>
      </div>
      <div className="detail-row">
        <span>Amount · source units</span>
        <b>{amount(tx.amount)}</b>
      </div>
      <div className="detail-row">
        <span>Threshold</span>
        <b>{percent(tx.threshold)}</b>
      </div>
      <div className="detail-row">
        <span>Observed label</span>
        <b>
          {tx.label == null
            ? "Unknown"
            : tx.label === 1
              ? "Fraud"
              : "Legitimate"}
        </b>
      </div>
      <code className="wrap-code">{tx.model_version}</code>
      <button
        className="secondary full"
        disabled={busy}
        onClick={explainRecord}
      >
        <FlaskConical size={13} />
        {busy ? "Computing…" : "Explain selected record"}
      </button>
      {explain && (
        <div className="context-shap">
          {!explain.matches_stored_prediction && (
            <p className="error-text">
              Active-model explanation differs from the stored prediction
              version.
            </p>
          )}
          {explain.features.slice(0, 5).map((f) => (
            <div className="detail-row" key={f.feature}>
              <code>{f.feature}</code>
              <b>
                {f.contribution > 0 ? "+" : ""}
                {f.contribution.toFixed(3)}
              </b>
            </div>
          ))}
          <p className="muted">
            Anonymized contributions; no merchant or behavioral meaning is
            inferred.
          </p>
        </div>
      )}
      <button className="text-button" onClick={() => onSelect(id)}>
        Open full transaction
        <ArrowRight size={12} />
      </button>
    </div>
  ) : (
    <Loading />
  );
}
function EntityEvidence({
  id,
  fail,
}: {
  id: string;
  fail: (e: unknown) => void;
}) {
  const [entity, setEntity] = useState<{
    label: string;
    kind: string;
    neighbors: { id: string; label: string }[];
  } | null>(null);
  useEffect(() => {
    api<typeof entity>("/entities/" + encodeURIComponent(id))
      .then(setEntity)
      .catch(fail);
  }, [id]);
  return entity ? (
    <div className="context-record">
      <span className="badge neutral">SYNTHETIC {entity.kind}</span>
      <h3>{entity.label}</h3>
      <p className="muted">
        Separate artificial relational fixture. It does not establish ULB
        relationships.
      </p>
      <div className="detail-row">
        <span>Direct neighbors</span>
        <b>{entity.neighbors.length}</b>
      </div>
      <a className="secondary full" href={"#graph/" + encodeURIComponent(id)}>
        Explore neighborhood
        <Network size={13} />
      </a>
    </div>
  ) : (
    <Loading />
  );
}
