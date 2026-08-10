import { useState, useRef, useEffect } from "react";

/**
 * Renders a small amber marginal tab after a claim. Clicking it reveals
 * exactly where the claim came from — the project's "strict source
 * grounding" requirement made visible as an interaction, not just a
 * footer disclaimer.
 */
export default function Citation({ index = 1, label, section }) {
  const [open, setOpen] = useState(false);
  const ref = useRef(null);

  useEffect(() => {
    function onClick(e) {
      if (ref.current && !ref.current.contains(e.target)) setOpen(false);
    }
    document.addEventListener("mousedown", onClick);
    return () => document.removeEventListener("mousedown", onClick);
  }, []);

  return (
    <span className="relative" ref={ref}>
      <button
        type="button"
        className="cite-tab"
        onClick={() => setOpen((v) => !v)}
        aria-expanded={open}
        aria-label={`Show source ${index}`}
      >
        {index}
      </button>
      {open && (
        <span
          role="tooltip"
          className="animate-fade-up absolute left-1/2 top-full z-20 mt-2 w-60 -translate-x-1/2 rounded-md border border-ledger-950/15 bg-ledger-950 px-3 py-2.5 text-left shadow-lg"
        >
          <span className="block font-mono text-[0.65rem] uppercase tracking-wider text-amber-500">
            Source
          </span>
          <span className="mt-1 block text-xs leading-snug text-parchment-100">{label}</span>
          {section && (
            <span className="mt-0.5 block text-[0.7rem] leading-snug text-parchment-100/60">
              {section}
            </span>
          )}
        </span>
      )}
    </span>
  );
}
