// Tarjeta de métrica: KPI del dashboard (variant="surface") o bloque dentro de una tarjeta ("inset").
export default function StatCard({ label, value, hint, icon, strong, variant = 'surface' }) {
  return (
    <div className={variant === 'inset' ? 'surface-inset p-4' : 'surface p-5'}>
      <div className="flex items-center justify-between gap-2">
        <p className="font-mono text-stamp tracking-stamp uppercase text-ink-soft">{label}</p>
        {icon && <span className="flex text-brand" aria-hidden="true">{icon}</span>}
      </div>
      <p
        className={`mt-1 ${
          strong ? 'font-mono text-2xl font-bold text-brand' : variant === 'inset' ? 'font-mono text-lg font-semibold text-ink' : 'text-2xl font-bold text-ink'
        }`}
      >
        {value}
      </p>
      {hint && <p className="text-xs text-ink-soft">{hint}</p>}
    </div>
  )
}
