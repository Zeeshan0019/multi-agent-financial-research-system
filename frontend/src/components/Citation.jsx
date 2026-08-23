import { useState, useRef, useEffect, useLayoutEffect, useCallback } from "react";
import { createPortal } from "react-dom";

/**
 * A small amber citation tab. Clicking it opens a popover showing exactly
 * where a claim came from (source label, page, and the quoted passage).
 *
 * The popover is rendered in a portal on document.body and positioned with
 * position:fixed, anchored to the tab's on-screen rect. The portal is
 * essential: several ancestors use CSS transforms (card hover, fade-up
 * animations), and a transformed ancestor turns position:fixed into
 * position:absolute relative to itself — which is what caused the popover to
 * clip at the panel edge. Rendering on body escapes all of them. The popover
 * then clamps to the viewport on all four sides.
 */
export default function Citation({ index = 1, label, page, section, snippet }) {
  const [open, setOpen] = useState(false);
  const [pos, setPos] = useState(null); // null until measured -> avoids flash
  const btnRef = useRef(null);
  const popRef = useRef(null);

  const reposition = useCallback(() => {
    if (!btnRef.current || !popRef.current) return;
    const MARGIN = 10;
    const rect = btnRef.current.getBoundingClientRect();
    const pop = popRef.current;
    const popW = pop.offsetWidth || 288;
    const popH = pop.offsetHeight || 160;
    const vw = window.innerWidth;
    const vh = window.innerHeight;

    // Horizontal: centre on the tab, then clamp fully into the viewport.
    let left = rect.left + rect.width / 2 - popW / 2;
    left = Math.max(MARGIN, Math.min(left, vw - popW - MARGIN));

    // Vertical: prefer below the tab; flip above if it would overflow.
    let top = rect.bottom + 8;
    if (top + popH > vh - MARGIN) {
      const above = rect.top - popH - 8;
      top = above >= MARGIN ? above : Math.max(MARGIN, vh - popH - MARGIN);
    }
    setPos({ top, left });
  }, []);

  // Measure after the popover mounts (two rAFs so layout + paint have settled).
  useLayoutEffect(() => {
    if (!open) return;
    setPos(null);
    let raf2;
    const raf1 = requestAnimationFrame(() => {
      raf2 = requestAnimationFrame(reposition);
    });
    return () => {
      cancelAnimationFrame(raf1);
      if (raf2) cancelAnimationFrame(raf2);
    };
  }, [open, reposition, snippet, section, label]);

  // Close on outside click; close on scroll/resize (anchor moved).
  useEffect(() => {
    if (!open) return;
    function onDocClick(e) {
      if (
        btnRef.current && !btnRef.current.contains(e.target) &&
        popRef.current && !popRef.current.contains(e.target)
      ) {
        setOpen(false);
      }
    }
    function onReflow() { setOpen(false); }
    document.addEventListener("mousedown", onDocClick);
    window.addEventListener("scroll", onReflow, true);
    window.addEventListener("resize", onReflow);
    return () => {
      document.removeEventListener("mousedown", onDocClick);
      window.removeEventListener("scroll", onReflow, true);
      window.removeEventListener("resize", onReflow);
    };
  }, [open]);

  const popover = open ? createPortal(
    <div
      ref={popRef}
      role="tooltip"
      style={{
        position: "fixed",
        top: pos ? pos.top : -9999,
        left: pos ? pos.left : -9999,
        width: "min(288px, calc(100vw - 20px))",
        visibility: pos ? "visible" : "hidden",
        zIndex: 2147483647,
      }}
      className="rounded-lg border border-amber-500/25 bg-ledger-950 px-3.5 py-3 text-left shadow-2xl"
    >
      <div className="flex items-center justify-between gap-2">
        <span className="font-mono text-[0.65rem] uppercase tracking-wider text-amber-500">
          Source
        </span>
        {page != null && page !== "" && (
          <span className="shrink-0 font-mono text-[0.6rem] font-bold text-amber-400 bg-amber-500/10 border border-amber-500/30 rounded px-1.5 py-0.5">
            Page {page}
          </span>
        )}
      </div>
      {label && (
        <div className="mt-1.5 text-xs font-semibold leading-snug text-parchment-100 break-words">
          {label}
        </div>
      )}
      {section && (
        <div className="mt-1 text-[0.7rem] leading-snug text-parchment-100/60 break-words">
          {section}
        </div>
      )}
      {snippet && (
        <div className="mt-2 max-h-36 overflow-y-auto border-l-2 border-amber-500/40 pl-2 text-[0.7rem] italic leading-snug text-parchment-100/80 break-words">
          &ldquo;{snippet}&rdquo;
        </div>
      )}
    </div>,
    document.body
  ) : null;

  return (
    <>
      <button
        ref={btnRef}
        type="button"
        className="cite-tab"
        onClick={() => setOpen((v) => !v)}
        aria-expanded={open}
        aria-label={`Show source ${index}`}
      >
        {index}
      </button>
      {popover}
    </>
  );
}
