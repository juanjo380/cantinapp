export default function PageHeader({ title, subtitle, children }) {
  return (
    <header className="mb-6 flex flex-col gap-4 md:mb-10 md:flex-row md:items-end md:justify-between">
      <div className="flex flex-col gap-2">
        <h1 className="text-3xl text-ink sm:text-4xl">{title}</h1>
        {subtitle && <p className="max-w-2xl text-sm font-medium text-ink-soft">{subtitle}</p>}
      </div>
      {children && <div className="flex flex-wrap items-center gap-2">{children}</div>}
    </header>
  )
}
