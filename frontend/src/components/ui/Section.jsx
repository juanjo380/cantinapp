// Bloque de contenido con título opcional y acciones a la derecha.
export default function Section({ title, label = title, actions, className = '', children }) {
  return (
    <section aria-label={label} className={`surface p-5 ${className}`.trim()}>
      {(title || actions) && (
        <div className="mb-3 flex flex-wrap items-center justify-between gap-2">
          {title && <h2 className="text-base font-semibold text-ink">{title}</h2>}
          {actions && <div className="flex flex-wrap items-center gap-2">{actions}</div>}
        </div>
      )}
      {children}
    </section>
  )
}
