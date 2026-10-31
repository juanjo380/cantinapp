// Tarjeta de métrica: KPI del dashboard (variant="surface") o bloque dentro de una tarjeta ("inset").
export default function StatCard({ label, value, hint, icon, strong, variant = 'surface' }) {
  if (variant === 'inset') {
    return (
      <div className="surface-inset p-4">
        <p className="text-stamp font-bold tracking-stamp uppercase text-ink-soft">{label}</p>
        <p className={`mt-1 font-mono font-bold ${strong ? 'text-2xl text-brand-ink' : 'text-lg text-ink'}`}>{value}</p>
        {hint && <p className="text-xs font-medium text-ink-soft">{hint}</p>}
      </div>
    )
  }

  return (
    <div className="surface surface-lift relative flex min-h-36 flex-col justify-between gap-3 overflow-hidden p-5">
      <div className="flex items-start justify-between gap-2">
        <p className="text-xs font-bold tracking-widest uppercase text-ink-soft">{label}</p>
        {icon && <span className="flex text-brand" aria-hidden="true">{icon}</span>}
      </div>
      <div>
        <p className="font-mono text-3xl font-bold break-words text-ink sm:text-4xl">{value}</p>
        {hint && <p className="mt-1 text-sm font-medium text-ink-soft">{hint}</p>}
      </div>
      <svg className="pointer-events-none absolute -right-4 -bottom-4 h-16 w-16 text-line" viewBox="0 0 100 100" aria-hidden="true">
        <circle cx="50" cy="50" r="40" stroke="currentColor" strokeWidth="4" fill="none" strokeDasharray="10 5" />
      </svg>
    </div>
  )
}
