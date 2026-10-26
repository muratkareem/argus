import { useEffect, useState } from "react";
import {
  ArrowRight,
  Database,
  FileSearch,
  LoaderCircle,
  Save,
  ShieldCheck,
  Sparkles,
} from "lucide-react";
import { api, send } from "../api";
import { Panel, Empty } from "../ui";
import type { Settings } from "../types";
type Source = {
  id: string;
  kind: string;
  label: string;
  provenance: string;
  model_version?: string;
};
type Context = {
  evidence: Record<string, unknown>;
  sources: Source[];
  scope: { transaction_id: number | null; case_id: number | null };
  boundary: string;
};
type Answer = Context & {
  interpretation: string;
  model: string;
  warning: string;
  generated_at: string;
  citation_audit?: { status: string; warning?: string };
};
export function CopilotWorkspace({
  settings,
  fail,
  notify,
  onSelect,
}: {
  settings: Settings | null;
  fail: (e: unknown) => void;
  notify: (s: string) => void;
  onSelect: (id: number) => void;
}) {
  const [txId, setTxId] = useState(""),
    [caseId, setCaseId] = useState(() => location.hash.split("/")[1] ?? ""),
    [question, setQuestion] = useState(
      "Summarize the recorded facts, model outputs, uncertainty, and next investigative steps. Cite supplied source IDs.",
    ),
    [context, setContext] = useState<Context | null>(null),
    [answer, setAnswer] = useState<Answer | null>(null),
    [busy, setBusy] = useState(false),
    [loading, setLoading] = useState(false),
    [saving, setSaving] = useState(false);
  useEffect(() => {
    const change = () => setCaseId(location.hash.split("/")[1] ?? "");
    addEventListener("hashchange", change);
    return () => removeEventListener("hashchange", change);
  }, []);
  async function load() {
    setLoading(true);
    try {
      const params = new URLSearchParams({
        ...(txId ? { transaction_id: txId } : {}),
        ...(caseId ? { case_id: caseId } : {}),
      });
      setContext(await api<Context>("/copilot/context?" + params));
      setAnswer(null);
    } catch (e) {
      setContext(null);
      fail(e);
    } finally {
      setLoading(false);
    }
  }
  const matches =
    context &&
    context.scope.transaction_id === (Number(txId) || null) &&
    context.scope.case_id === (Number(caseId) || null);
  async function ask() {
    if (!context || !matches) return;
    setBusy(true);
    setAnswer(null);
    try {
      const result = await api<Omit<Answer, "generated_at">>(
        "/copilot",
        send("POST", { question, ...context.scope }),
      );
      setAnswer({ ...result, generated_at: new Date().toISOString() });
    } catch (e) {
      fail(e);
    } finally {
      setBusy(false);
    }
  }
  async function save() {
    if (!answer?.scope.case_id) return;
    setSaving(true);
    try {
      await api(
        `/cases/${answer.scope.case_id}/notes`,
        send("POST", {
          body: `LLM-GENERATED INTERPRETATION — analyst verification required\nModel: ${answer.model}\nGenerated: ${answer.generated_at}\nSources: ${answer.sources.map((s) => s.id).join(", ")}\n\n${answer.interpretation}`,
        }),
      );
      notify(
        "Generated interpretation saved as an explicitly labeled analyst note.",
      );
    } catch (e) {
      fail(e);
    } finally {
      setSaving(false);
    }
  }
  function open(source: Source) {
    if (source.kind === "Transaction")
      onSelect(Number(source.id.split(":")[1]));
    else
      location.hash =
        source.kind === "Case"
          ? `investigations/${source.id.split(":")[1]}`
          : `graph/${encodeURIComponent(source.id.slice("entity:".length))}`;
  }
  return (
    <div className="copilot-workspace">
      <Panel title="Evidence selection" meta={<Database size={13} />}>
        <div className="copilot-selection">
          <label className="field">
            Transaction ID
            <input
              type="number"
              min="1"
              disabled={busy || loading}
              aria-label="Copilot transaction ID"
              value={txId}
              onChange={(e) => setTxId(e.target.value)}
            />
          </label>
          <label className="field">
            Investigation ID
            <input
              type="number"
              min="1"
              disabled={busy || loading}
              aria-label="Copilot case ID"
              value={caseId}
              onChange={(e) => setCaseId(e.target.value)}
            />
          </label>
          <button
            className="secondary full"
            disabled={busy || loading || (!txId && !caseId)}
            onClick={load}
          >
            {loading ? (
              <LoaderCircle className="spin" size={13} />
            ) : (
              <FileSearch size={13} />
            )}
            Load selected evidence
          </button>
          {context ? (
            <>
              <div className="filter-group-label">
                RETRIEVED SOURCES · {context.sources.length}
              </div>
              {context.sources.map((source) => (
                <button
                  className="copilot-source"
                  key={source.id}
                  onClick={() => open(source)}
                >
                  <span className="source-kind">{source.kind}</span>
                  <b>{source.label}</b>
                  <small>
                    {source.provenance} · {source.id}
                  </small>
                  <ArrowRight size={11} />
                </button>
              ))}
              <details>
                <summary>Inspect structured context</summary>
                <pre>{JSON.stringify(context.evidence, null, 2)}</pre>
              </details>
              {!matches && (
                <p className="error-text">
                  Selection changed. Reload evidence before analysis.
                </p>
              )}
            </>
          ) : (
            <p className="muted">
              Select a stored record to inspect the exact context supplied to
              the model. Evidence retrieval works while Copilot is disabled.
            </p>
          )}
          <div className="copilot-boundary">
            <ShieldCheck size={15} />
            <span>
              Read-only retrieval. No SQL, shell, or automatic case actions.
            </span>
          </div>
        </div>
      </Panel>
      <Panel
        title="Investigation Copilot"
        meta={
          <span
            className={
              "badge " + (settings?.ollama_enabled ? "success" : "neutral")
            }
          >
            {settings?.ollama_enabled ? settings.ollama_model : "Disabled"}
          </span>
        }
      >
        <div className="copilot-analysis">
          {!settings?.ollama_enabled && (
            <div className="setup-box">
              <b>Optional integration is disabled</b>
              <p>
                Load evidence without an LLM, or enable a local Ollama model in
                the server configuration.
              </p>
              <pre>
                ARGUS_OLLAMA_ENABLED=true
                <br />
                ARGUS_OLLAMA_MODEL=your-installed-model
              </pre>
            </div>
          )}
          <div className="prompt-presets">
            <span>ANALYSIS MODE</span>
            {[
              [
                "Case summary",
                "Summarize only the recorded facts, model outputs and uncertainty. Cite supplied source IDs.",
              ],
              [
                "Next steps",
                "Suggest next investigative steps based only on supplied evidence. Distinguish suggestions from facts and do not execute actions. Cite source IDs.",
              ],
              [
                "Model interpretation",
                "Explain the supplied model score and SHAP values if available. State provenance, model-version mismatches and limits of anonymized features. Cite source IDs.",
              ],
            ].map(([name, prompt]) => (
              <button
                className="secondary"
                key={name}
                disabled={busy}
                onClick={() => setQuestion(prompt)}
              >
                {name}
              </button>
            ))}
          </div>
          <label className="field">
            Question
            <textarea
              disabled={busy}
              aria-label="Copilot question"
              maxLength={2000}
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
            />
          </label>
          <button
            className="primary"
            disabled={
              !settings?.ollama_enabled || !matches || !question.trim() || busy
            }
            onClick={ask}
          >
            {busy ? (
              <LoaderCircle className="spin" size={14} />
            ) : (
              <Sparkles size={14} />
            )}
            Analyze selected evidence
          </button>
          {busy && (
            <div className="copilot-wait" role="status">
              Local model is generating an interpretation. Evidence remains
              unchanged.
            </div>
          )}
          {answer ? (
            <article className="copilot-interpretation">
              <header>
                <span className="mini-tag">
                  LLM INTERPRETATION · VERIFY CLAIMS
                </span>
                <small>
                  {answer.model} ·{" "}
                  {new Date(answer.generated_at).toLocaleTimeString()}
                </small>
              </header>
              <div className="model-score-boundary">
                ML scores are uncalibrated review signals. They are not
                probabilities, confidence estimates, or proof of fraud.
              </div>
              {answer.citation_audit?.status === "unverified_text" && (
                <div className="error-text">
                  {answer.citation_audit.warning}
                </div>
              )}
              <div className="llm-text">{answer.interpretation}</div>
              <div className="interpretation-warning">{answer.warning}</div>
              {answer.scope.case_id && (
                <button className="secondary" disabled={saving} onClick={save}>
                  <Save size={13} />
                  Save as labeled case note
                </button>
              )}
            </article>
          ) : (
            !busy && (
              <Empty>
                <Sparkles size={26} />
                Load evidence, choose an analysis mode, and review the generated
                interpretation against the source records.
              </Empty>
            )
          )}
          <p className="muted">
            Database records, stored ML predictions, active-model SHAP, analyst
            opinions, and generated interpretations remain distinct. Synthetic
            entities never establish ULB relationships.
          </p>
        </div>
      </Panel>
    </div>
  );
}
