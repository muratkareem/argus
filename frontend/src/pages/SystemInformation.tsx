import { useEffect, useState } from "react";
import { api } from "../api";
import { Empty, Panel } from "../ui";
import type { Dataset, Models, Settings } from "../types";

export function SystemInformation({
  settings,
  revision,
  reconnect,
}: {
  settings: Settings | null;
  revision: number;
  reconnect: () => void;
}) {
  const [health, setHealth] = useState<{
      status: string;
      database: string;
    } | null>(null),
    [datasets, setDatasets] = useState<Dataset[]>([]),
    [models, setModels] = useState<Models | null>(null),
    [key, setKey] = useState(
      () => sessionStorage.getItem("argus-api-key") ?? "",
    ),
    [error, setError] = useState(""),
    [saved, setSaved] = useState(false);
  useEffect(() => {
    let cancelled = false;
    Promise.all([
      api<{ status: string; database: string }>("/health"),
      api<Dataset[]>("/datasets"),
      api<Models>("/models"),
    ])
      .then(([h, d, m]) => {
        if (!cancelled) {
          setHealth(h);
          setDatasets(d);
          setModels(m);
          setError("");
        }
      })
      .catch((e) => {
        if (!cancelled) setError(e.message);
      });
    return () => {
      cancelled = true;
    };
  }, [revision]);
  const experiment = models?.experiments.find(
    (e) => e.version === models.active_version,
  );
  return (
    <>
      <div className="two-grid">
        <Panel title="Environment">
          <div className="padded">
            {error && (
              <p className="error-text" role="alert">
                {error}
              </p>
            )}
            {[
              ["System health", health?.status ?? "Unavailable"],
              [
                "Database",
                settings?.database ?? health?.database ?? "Unavailable",
              ],
              [
                "Authentication",
                settings?.authentication ?? "Connect to inspect",
              ],
              [
                "Upload limit",
                settings ? `${settings.max_upload_mib} MiB` : "Unavailable",
              ],
              [
                "Active algorithm",
                experiment?.selected_model ?? "No active model",
              ],
              ["Model version", models?.active_version ?? "Untrained"],
              [
                "Last verified evaluation",
                experiment
                  ? new Date(experiment.created_at).toLocaleString()
                  : "Not recorded",
              ],
            ].map(([label, value]) => (
              <div className="detail-row" key={label}>
                <span>{label}</span>
                <b className="wrap-code">{value}</b>
              </div>
            ))}
            <p className="muted">
              Evaluation date comes from the active experiment artifact. Health
              confirms API/database availability; it does not certify model
              effectiveness.
            </p>
          </div>
        </Panel>
        <Panel title="API connection">
          <form
            className="padded"
            onSubmit={(event) => {
              event.preventDefault();
              if (key.trim())
                sessionStorage.setItem("argus-api-key", key.trim());
              else sessionStorage.removeItem("argus-api-key");
              setSaved(true);
              reconnect();
            }}
          >
            <label className="field">
              API access key
              <input
                type="password"
                autoComplete="off"
                value={key}
                onChange={(event) => {
                  setKey(event.target.value);
                  setSaved(false);
                }}
              />
            </label>
            <p className="muted">
              When the backend uses ARGUS_API_KEY, enter the same key here. It
              stays in this tab’s session storage and is sent only to the local
              API. Leave blank for the default local setup.
            </p>
            <button className="primary" type="submit">
              Apply connection key
            </button>
            {saved && <p role="status">Connection settings applied.</p>}
          </form>
        </Panel>
      </div>
      <Panel title="Dataset metadata">
        {datasets.length ? (
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Dataset</th>
                  <th>Provenance</th>
                  <th>Stored rows</th>
                  <th>Duplicates skipped</th>
                  <th>Imported</th>
                </tr>
              </thead>
              <tbody>
                {datasets.map((d) => (
                  <tr key={d.id}>
                    <td>{d.name}</td>
                    <td>{d.provenance}</td>
                    <td>{d.rows.toLocaleString()}</td>
                    <td>{d.duplicates.toLocaleString()}</td>
                    <td>{new Date(d.created_at).toLocaleString()}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <Empty>No dataset metadata available.</Empty>
        )}
      </Panel>
      <Panel title="Research boundaries">
        <div className="padded">
          <p>
            ARGUS is an educational credit card fraud research prototype. It has
            no bank integration or compliance certification. API key access is
            optional; keep deployment private.
          </p>
          <p>
            ULB uses anonymized V1–V28 features and contains no cardholder,
            merchant, or account identities. The separate relationship graph is
            an artificial fixture.
          </p>
          <p>
            Model probability estimates are uncalibrated. A flagged transaction
            requires analyst review. Synthetic experiment results do not
            establish performance on real card transactions.
          </p>
          <details>
            <summary>Inference feature schema</summary>
            <p className="mono wrap-code">
              {settings?.schema.join(", ") ?? "Schema unavailable"}
            </p>
          </details>
          <a
            className="secondary"
            href="/api/v1/health"
            target="_blank"
            rel="noreferrer"
          >
            Inspect system health
          </a>
        </div>
      </Panel>
    </>
  );
}
