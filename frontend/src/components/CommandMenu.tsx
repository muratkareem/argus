import { useEffect, useRef, useState } from "react";
import { ArrowRight, Search, X } from "lucide-react";
import { api } from "../api";
type SearchResult = { kind: string; id: string; label: string; detail: string };
export function CommandMenu({
  pages,
  close,
  onTransaction,
}: {
  pages: { id: string; label: string }[];
  close: () => void;
  onTransaction: (id: number) => void;
}) {
  const [q, setQ] = useState(""),
    [results, setResults] = useState<SearchResult[]>([]),
    [error, setError] = useState(""),
    [searching, setSearching] = useState(false);
  const input = useRef<HTMLInputElement>(null);
  useEffect(() => {
    const previous = document.activeElement as HTMLElement;
    input.current?.focus();
    return () => previous?.focus();
  }, []);
  useEffect(() => {
    let cancelled = false;
    setError("");
    setResults([]);
    setSearching(Boolean(q.trim()));
    if (!q.trim()) {
      setResults([]);
      return;
    }
    const timer = setTimeout(
      () =>
        api<{ results: SearchResult[] }>(
          "/search?q=" + encodeURIComponent(q.trim()),
        )
          .then((d) => {
            if (!cancelled) {
              setResults(d.results);
              setSearching(false);
            }
          })
          .catch((e) => {
            if (!cancelled) {
              setError(e.message);
              setSearching(false);
            }
          }),
      180,
    );
    return () => {
      cancelled = true;
      clearTimeout(timer);
    };
  }, [q]);
  const matches = pages.filter((p) =>
    p.label.toLowerCase().includes(q.toLowerCase()),
  );
  function open(result: SearchResult) {
    close();
    if (result.kind === "Transaction") onTransaction(Number(result.id));
    else
      location.hash =
        result.kind === "Case"
          ? `investigations/${result.id}`
          : `graph/${encodeURIComponent(result.id)}`;
  }
  return (
    <div className="overlay command-overlay" onClick={close}>
      <section
        className="command-menu"
        role="dialog"
        aria-label="Workspace search"
        aria-modal="true"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="command-input">
          <Search size={18} />
          <input
            ref={input}
            aria-label="Search workspace"
            placeholder="Transactions, investigations, synthetic entities…"
            value={q}
            onChange={(e) => setQ(e.target.value)}
          />
          <button
            className="icon-button"
            onClick={close}
            aria-label="Close workspace search"
          >
            <X size={16} />
          </button>
        </div>
        <div className="command-results">
          {q && (
            <>
              <div className="command-group">DATABASE RECORDS</div>
              {results.map((r) => (
                <button
                  className="command-result"
                  aria-label={`Open ${r.kind} ${r.label}`}
                  key={r.kind + r.id}
                  onClick={() => open(r)}
                >
                  <span>
                    {r.label}
                    <small>
                      {r.kind} · {r.detail}
                    </small>
                  </span>
                  <ArrowRight size={14} />
                </button>
              ))}
              {searching && (
                <p className="muted padded" role="status">
                  Searching stored records…
                </p>
              )}
              {!searching && !results.length && !error && (
                <p className="muted padded">No matching records.</p>
              )}
              {error && (
                <div className="command-error" role="alert">
                  {error}
                </div>
              )}
            </>
          )}
          <div className="command-group">APPLICATIONS</div>
          {matches.map((p) => (
            <a
              className="command-result"
              key={p.id}
              href={"#" + p.id}
              onClick={close}
            >
              <span>{p.label}</span>
              <ArrowRight size={14} />
            </a>
          ))}
        </div>
        <div className="command-footer">
          Tab to a result · Enter to open · Esc to close
        </div>
      </section>
    </div>
  );
}
