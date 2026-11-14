import { Empty } from "../ui";

export type Contribution = {
  feature: string;
  contribution: number;
  value?: number;
};
export function ExplanationContributions({
  features,
  outputSpace,
  baseValue,
  modelVersion,
  caveat,
}: {
  features: Contribution[];
  outputSpace?: string;
  baseValue?: number;
  modelVersion?: string;
  caveat?: string;
}) {
  const ordered = [...features].sort(
    (a, b) => Math.abs(b.contribution) - Math.abs(a.contribution),
  );
  const maximum = Math.max(
    ...ordered.map((f) => Math.abs(f.contribution)),
    1e-12,
  );
  return (
    <div className="contribution-summary">
      <p className="explanation-intro">How the model arrived at this score</p>
      <div className="contribution-columns">
        {[
          { title: "Raises the score", positive: true },
          { title: "Lowers the score", positive: false },
        ].map((group) => {
          const rows = ordered
            .filter((f) =>
              group.positive ? f.contribution > 0 : f.contribution < 0,
            )
            .slice(0, 5);
          return (
            <section key={group.title} aria-label={group.title}>
              <h3>
                {group.positive ? "↑" : "↓"} {group.title}
              </h3>
              {rows.length ? (
                <ol>
                  {rows.map((f) => (
                    <li key={f.feature}>
                      <div>
                        <span className="mono">{f.feature}</span>
                        <b className="mono">
                          {f.contribution > 0 ? "+" : ""}
                          {f.contribution.toFixed(3)}
                        </b>
                      </div>
                      <span className="contribution-track" aria-hidden="true">
                        <i
                          className={group.positive ? "positive" : "negative"}
                          style={{
                            width: `${(Math.abs(f.contribution) / maximum) * 100}%`,
                          }}
                        />
                      </span>
                    </li>
                  ))}
                </ol>
              ) : (
                <Empty>No contributions in this direction.</Empty>
              )}
            </section>
          );
        })}
      </div>
      <p className="explanation-caveat">
        Contributions describe model behavior, not causal evidence of fraud.
        V1–V28 are anonymized components.
      </p>
      <details className="technical-details">
        <summary>Explanation details and all features</summary>
        <p>
          SHAP output: {outputSpace ?? "See model metadata"}.{" "}
          {baseValue != null && <>Base value: {baseValue.toFixed(4)}.</>}
        </p>
        {modelVersion && (
          <p>
            Model version: <code className="wrap-code">{modelVersion}</code>
          </p>
        )}
        {caveat && <p>{caveat}</p>}
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Feature</th>
                <th>Contribution</th>
              </tr>
            </thead>
            <tbody>
              {ordered.map((f) => (
                <tr key={f.feature}>
                  <td className="mono">{f.feature}</td>
                  <td className="mono">
                    {f.contribution > 0 ? "+" : ""}
                    {f.contribution.toPrecision(5)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </details>
    </div>
  );
}
