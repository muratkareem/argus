import { useEffect, useRef, useState } from "react";
import cytoscape from "cytoscape";
import {
  ArrowRight,
  Focus,
  Network,
  Plus,
  Search,
  ChevronRight,
} from "lucide-react";
import { api, send } from "../api";
import { Panel, Empty } from "../ui";
import type { Case } from "../types";
type NodeData = {
  id: string;
  label: string;
  kind: string;
  shared_accounts?: number;
};
type GraphData = {
  nodes: { data: NodeData }[];
  edges: cytoscape.ElementDefinition[];
  total_entities: number;
};
type EntityDetail = NodeData & {
  provenance: string;
  neighbors: NodeData[];
  case_ids: number[];
};
const selectedRoot = () =>
  decodeURIComponent(location.hash.split("/")[1] ?? "");
export function GraphIntelligence({
  fail,
  notify,
}: {
  fail: (e: unknown) => void;
  notify: (s: string) => void;
}) {
  const host = useRef<HTMLDivElement>(null),
    instance = useRef<cytoscape.Core | null>(null);
  const [root, setRoot] = useState(selectedRoot),
    [depth, setDepth] = useState(1),
    [kind, setKind] = useState(""),
    [relation, setRelation] = useState(""),
    [shared, setShared] = useState(false),
    [graph, setGraph] = useState<GraphData | null>(null),
    [selected, setSelected] = useState<EntityDetail | null>(null),
    [cases, setCases] = useState<Case[]>([]),
    [caseId, setCaseId] = useState(""),
    [busy, setBusy] = useState(false);
  useEffect(() => {
    const changed = () => {
      setRoot(selectedRoot());
      setDepth(1);
    };
    addEventListener("hashchange", changed);
    api<Case[]>("/cases").then(setCases).catch(fail);
    return () => removeEventListener("hashchange", changed);
  }, []);
  async function inspect(id: string) {
    try {
      setSelected(
        await api<EntityDetail>("/entities/" + encodeURIComponent(id)),
      );
    } catch (e) {
      fail(e);
    }
  }
  useEffect(() => {
    let cancelled = false;
    const params = new URLSearchParams({
      depth: String(depth),
      ...(root ? { root } : {}),
      ...(kind ? { kind } : {}),
      ...(relation ? { relation } : {}),
      ...(shared ? { shared_only: "true" } : {}),
    });
    api<GraphData>("/intelligence/graph?" + params)
      .then((data) => {
        if (!cancelled) {
          setGraph(data);
          if (root) void inspect(root);
        }
      })
      .catch(fail);
    return () => {
      cancelled = true;
    };
  }, [root, depth, kind, relation, shared]);
  useEffect(() => {
    if (!host.current || !graph) return;
    const cy = cytoscape({
      container: host.current,
      maxZoom: 1.6,
      minZoom: 0.25,
      wheelSensitivity: 0.2,
      elements: [...graph.nodes, ...graph.edges],
      layout: {
        name: "cose",
        animate: false,
        nodeRepulsion: () => 12000,
        idealEdgeLength: () => 95,
      },
      style: [
        {
          selector: "node",
          style: {
            label: "data(label)",
            "font-size": 10,
            color: "#a8c0d1",
            "text-valign": "bottom",
            "text-margin-y": 8,
            "background-color": "#578f9d",
            width: 22,
            height: 22,
          },
        },
        {
          selector: 'node[kind="Account"]',
          style: {
            "background-color": "#729bc6",
            shape: "round-rectangle",
            width: 36,
            height: 30,
          },
        },
        {
          selector: 'node[kind="Device"]',
          style: {
            "background-color": "#8d9eac",
            shape: "diamond",
            width: 32,
            height: 32,
          },
        },
        {
          selector: "node[shared_accounts > 1]",
          style: {
            "background-color": "#d0a66e",
            "border-width": 3,
            "border-color": "#755d39",
            width: 38,
            height: 38,
          },
        },
        {
          selector: 'node[kind="Merchant"]',
          style: {
            "background-color": "#9a8db9",
            shape: "hexagon",
            width: 28,
            height: 28,
          },
        },
        {
          selector: "edge",
          style: {
            width: 1.3,
            "line-color": "#3c566a",
            "target-arrow-color": "#4f728c",
            "target-arrow-shape": "triangle",
            "curve-style": "bezier",
            label: "data(label)",
            "font-size": 7,
            color: "#58758a",
            "text-rotation": "autorotate",
            "text-margin-y": -6,
          },
        },
        {
          selector: ":selected",
          style: {
            "background-color": "#d6e7ed",
            "border-width": 3,
            "border-color": "#88c2cf",
            "line-color": "#8dc1cf",
          },
        },
      ],
    });
    instance.current = cy;
    cy.on("tap", "node", (event) => void inspect(event.target.id()));
    return () => {
      cy.destroy();
      instance.current = null;
    };
  }, [graph]);
  async function createCase() {
    if (!selected) return;
    setBusy(true);
    try {
      const record = await api<Case>(
        "/cases",
        send("POST", {
          title: `Review synthetic ${selected.label}`,
          priority:
            selected.kind === "Device" &&
            selected.neighbors.filter((n) => n.kind === "Account").length > 1
              ? "High"
              : "Medium",
          entity_ids: [selected.id],
        }),
      );
      notify(
        `Investigation #${record.id} created with synthetic entity evidence.`,
      );
      location.hash = `investigations/${record.id}`;
    } catch (e) {
      fail(e);
    } finally {
      setBusy(false);
    }
  }
  async function link() {
    if (!selected || !caseId) return;
    try {
      await api(
        `/cases/${caseId}/entities`,
        send("POST", { entity_id: selected.id }),
      );
      await inspect(selected.id);
      notify(`Synthetic entity linked to case #${caseId}.`);
    } catch (e) {
      fail(e);
    }
  }
  function focus(id: string) {
    setRoot(id);
    setDepth(1);
    setKind("");
    void inspect(id);
  }
  return (
    <>
      <div className="graph-context">
        <span className="badge neutral">SYNTHETIC RELATIONAL DATA</span>
        <p>
          Shared devices are structural cues in an artificial fixture. No ULB
          relationships or model-based fraud labels are inferred.
        </p>
      </div>
      <div className="graph-workspace">
        <Panel
          title="Relationship explorer"
          meta={
            <span className="mono muted">
              {graph?.nodes.length ?? 0} / {graph?.total_entities ?? 0} entities
            </span>
          }
        >
          <div className="graph-query-bar">
            <label className="field">
              Entity type
              <select
                aria-label="Graph entity type"
                value={kind}
                onChange={(e) => setKind(e.target.value)}
              >
                <option value="">All entities</option>
                {["Account", "Card", "Device", "Merchant", "Transaction"].map(
                  (k) => (
                    <option key={k}>{k}</option>
                  ),
                )}
              </select>
            </label>
            <label className="field">
              Relationship
              <select
                aria-label="Graph relationship type"
                value={relation}
                onChange={(e) => setRelation(e.target.value)}
              >
                <option value="">All relationships</option>
                {["owns", "uses", "initiates", "targets"].map((r) => (
                  <option key={r}>{r}</option>
                ))}
              </select>
            </label>
            <label className="checkbox-field">
              <input
                type="checkbox"
                checked={shared}
                onChange={(e) => setShared(e.target.checked)}
              />
              Shared-device cue
            </label>
            <button
              className="secondary"
              onClick={() => instance.current?.fit(undefined, 40)}
            >
              <Focus size={13} />
              Fit
            </button>
          </div>
          <div className="graph-breadcrumb">
            <button
              onClick={() => {
                setRoot("");
                setDepth(1);
                setKind("");
                setRelation("");
                setShared(false);
              }}
            >
              Full network
            </button>
            {root && (
              <>
                <ChevronRight size={12} />
                <span>{root}</span>
                <ChevronRight size={12} />
                <span>
                  {depth} hop{depth === 1 ? "" : "s"}
                </span>
              </>
            )}
            <button
              className="text-button"
              disabled={!root || depth >= 4}
              onClick={() => setDepth((d) => Math.min(4, d + 1))}
            >
              <Plus size={12} />
              Expand neighborhood
            </button>
          </div>
          <div className="graph-canvas" ref={host} />
          {graph?.nodes.length === 0 && (
            <Empty>
              No entities match the selected neighborhood and filters.
            </Empty>
          )}
          <div className="graph-status">
            <span>
              Drag nodes · scroll to zoom · pan canvas · select to inspect
            </span>
            <span className="legend">
              <i />
              Entity <i style={{ background: "#d0a66e" }} />
              Shared device
            </span>
          </div>
        </Panel>
        <Panel title="Entity context" meta={<Network size={14} />}>
          <div className="graph-inspector">
            <label className="field">
              Inspect a visible entity
              <select
                aria-label="Inspect graph entity"
                value={
                  graph?.nodes.some((n) => n.data.id === selected?.id)
                    ? (selected?.id ?? "")
                    : ""
                }
                onChange={(e) => {
                  if (e.target.value) void inspect(e.target.value);
                }}
              >
                <option value="">Select an entity…</option>
                {graph?.nodes.map((n) => (
                  <option key={n.data.id} value={n.data.id}>
                    {n.data.label}
                  </option>
                ))}
              </select>
            </label>
            {selected ? (
              <>
                <span className="badge neutral">SYNTHETIC {selected.kind}</span>
                <h3>{selected.label}</h3>
                <code>{selected.id}</code>
                <div className="detail-row">
                  <span>Direct connections</span>
                  <b>{selected.neighbors.length}</b>
                </div>
                {selected.kind === "Device" && (
                  <div className="detail-row">
                    <span>Account links</span>
                    <b>
                      {
                        selected.neighbors.filter((n) => n.kind === "Account")
                          .length
                      }
                    </b>
                  </div>
                )}
                <button
                  className="secondary full"
                  onClick={() => focus(selected.id)}
                >
                  <Search size={13} />
                  Explore neighborhood
                </button>
                <div className="filter-group-label">DIRECT NEIGHBORS</div>
                <div className="neighbor-list">
                  {selected.neighbors.map((n) => (
                    <button key={n.id} onClick={() => focus(n.id)}>
                      {n.label}
                      <small>{n.kind}</small>
                      <ArrowRight size={12} />
                    </button>
                  ))}
                </div>
                <div className="filter-group-label">INVESTIGATION LINKS</div>
                <div className="case-links">
                  {selected.case_ids.map((id) => (
                    <a
                      className="secondary"
                      key={id}
                      href={"#investigations/" + id}
                    >
                      Case #{id}
                      <ArrowRight size={12} />
                    </a>
                  ))}
                </div>
                <button
                  className="primary full"
                  disabled={busy}
                  onClick={createCase}
                >
                  <Plus size={13} />
                  Create entity investigation
                </button>
                <div className="inline-form">
                  <select
                    aria-label="Existing graph investigation"
                    value={caseId}
                    onChange={(e) => setCaseId(e.target.value)}
                  >
                    <option value="">Link existing case…</option>
                    {cases.map((c) => (
                      <option key={c.id} value={c.id}>
                        #{c.id} {c.title}
                      </option>
                    ))}
                  </select>
                  <button
                    className="secondary"
                    disabled={!caseId}
                    onClick={link}
                  >
                    Link
                  </button>
                </div>
                <p className="muted">
                  Entity links retain explicit synthetic provenance in case
                  reports. They are not evidence about real ULB cardholders.
                </p>
              </>
            ) : (
              <p className="muted">
                Select a node or use the accessible entity selector. Inspect
                relationships, expand neighborhoods, and link artificial
                entities to cases.
              </p>
            )}
          </div>
        </Panel>
      </div>
    </>
  );
}
