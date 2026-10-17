export default function AuthShell({ title, subtitle, children, footer }) {
  return (
    <main className="grid min-h-svh place-items-center bg-ground px-4 py-10">
      <div className="w-full max-w-md">
        <div className="mb-7 flex items-center justify-center gap-2.5">
          <span className="grid h-9 w-9 place-items-center rounded-md bg-brand text-lg font-black text-brand-contrast">
            C
          </span>
          <span className="text-2xl font-extrabold tracking-tight text-ink">CantinAPP</span>
        </div>
        <div className="rounded-lg border border-line bg-panel p-6 sm:p-8">
          <h1 className="text-xl font-bold tracking-tight text-ink">{title}</h1>
          <p className="mt-1 text-sm text-ink-soft">{subtitle}</p>
          <div className="mt-7">{children}</div>
        </div>
        {footer && <div className="mt-5 text-center text-sm text-ink-soft">{footer}</div>}
      </div>
    </main>
  )
}
