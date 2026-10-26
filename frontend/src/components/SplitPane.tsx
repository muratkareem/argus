import { useRef, useState } from "react";
import type { ReactNode } from "react";
export function SplitPane({
  storageKey,
  initial = 35,
  min = 20,
  max = 70,
  label,
  first,
  second,
}: {
  storageKey: string;
  initial?: number;
  min?: number;
  max?: number;
  label: string;
  first: ReactNode;
  second: ReactNode;
}) {
  const host = useRef<HTMLDivElement>(null);
  const [width, setWidth] = useState(() => {
    const saved = Number(localStorage.getItem(storageKey));
    return saved >= min && saved <= max ? saved : initial;
  });
  const update = (value: number) => {
    const next = Math.min(max, Math.max(min, value));
    setWidth(next);
    localStorage.setItem(storageKey, String(next));
  };
  return (
    <div
      ref={host}
      className="split-pane"
      style={{
        gridTemplateColumns: `minmax(0,${width}fr) 7px minmax(0,${100 - width}fr)`,
      }}
    >
      <div className="split-region">{first}</div>
      <div
        className="resize-handle"
        role="separator"
        aria-label={label}
        aria-orientation="vertical"
        aria-valuemin={min}
        aria-valuemax={max}
        aria-valuenow={Math.round(width)}
        tabIndex={0}
        onPointerDown={(event) => {
          event.preventDefault();
          event.currentTarget.setPointerCapture(event.pointerId);
        }}
        onPointerMove={(event) => {
          if (event.buttons !== 1 || !host.current) return;
          const bounds = host.current.getBoundingClientRect();
          update(((event.clientX - bounds.left) / bounds.width) * 100);
        }}
        onKeyDown={(event) => {
          if (["ArrowLeft", "ArrowRight", "Home", "End"].includes(event.key)) {
            event.preventDefault();
            update(
              event.key === "Home"
                ? min
                : event.key === "End"
                  ? max
                  : width + (event.key === "ArrowLeft" ? -2 : 2),
            );
          }
        }}
      />
      <div className="split-region">{second}</div>
    </div>
  );
}
