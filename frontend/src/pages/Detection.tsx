import { useEffect, useState } from "react";
import { Plus, LoaderCircle, ShieldCheck } from "lucide-react";
import { api } from "../api";
import { Panel, Empty } from "../ui";
import { PredictionForm } from "./PredictionForm";
import type { Dataset, Models } from "../types";
export default function Detection({
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
      <PredictionForm models={models} />
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
