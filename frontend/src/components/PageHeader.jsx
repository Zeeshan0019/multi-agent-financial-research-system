export default function PageHeader({ eyebrow, title, description, action }) {
  return (
    <div className="mb-8 flex items-start justify-between gap-6">
      <div>
        {eyebrow && (
          <p className="eyebrow mb-2 flex items-center gap-1.5">
            <span
              className="h-1.5 w-4 rounded-full"
              style={{ background: "linear-gradient(90deg,#8B5CF6,#14B8A6)" }}
            />
            {eyebrow}
          </p>
        )}
        <h1 className="font-display text-[1.75rem] font-semibold leading-tight text-ledger-950">
          {title}
        </h1>
        {description && (
          <p className="mt-1.5 max-w-xl text-sm leading-relaxed text-ledger-950/60">
            {description}
          </p>
        )}
      </div>
      {action && <div className="shrink-0 pt-1">{action}</div>}
    </div>
  );
}
