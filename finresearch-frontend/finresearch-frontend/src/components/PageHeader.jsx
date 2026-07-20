import React from "react";

export default function PageHeader({ eyebrow, title, description, actions }) {
  return (
    <div className="flex items-start justify-between gap-4 px-8 pt-8 pb-6 border-b border-ledger-950/10">
      <div>
        {eyebrow && (
          <p className="label text-amber-600 mb-1">{eyebrow}</p>
        )}
        <h1 className="text-2xl font-semibold text-ledger-950">{title}</h1>
        {description && (
          <p className="text-sm text-ledger-950/60 mt-1 max-w-2xl">{description}</p>
        )}
      </div>
      {actions && <div className="flex items-center gap-2 shrink-0">{actions}</div>}
    </div>
  );
}
