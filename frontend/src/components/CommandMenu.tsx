import { useEffect, useRef, useState } from "react";
import { ArrowRight, Search, X } from "lucide-react";
export function CommandMenu({
  pages,
  close,
}: {
  pages: { id: string; label: string }[];
  close: () => void;
  onTransaction: (id: number) => void;
}) {
  const [q, setQ] = useState("");
  const input = useRef<HTMLInputElement>(null);
  useEffect(() => {
    input.current?.focus();
  }, []);
  const matches = pages.filter((p) =>
    p.label.toLowerCase().includes(q.toLowerCase()),
  );
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
            placeholder="Find an application…"
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
        {!matches.length && (
          <p className="muted padded">No matching application.</p>
        )}
        <div className="command-footer">
          Tab to a result · Enter to open · Esc to close
        </div>
      </section>
    </div>
  );
}
