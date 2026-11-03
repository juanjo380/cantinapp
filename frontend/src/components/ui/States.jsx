import Alert from '@mui/material/Alert'
import Button from '@mui/material/Button'
import Skeleton from '@mui/material/Skeleton'
import ErrorOutlinedIcon from '@mui/icons-material/ErrorOutlined'
import InboxOutlinedIcon from '@mui/icons-material/InboxOutlined'
import { useEffect, useState } from 'react'

const times = (n) => Array.from({ length: n }, (_, i) => i)
const CELL_WIDTHS = ['45%', '20%', '15%', '20%'] // anchos variados: se lee como datos, no como bloques

function TableSkeleton({ rows }) {
  return (
    <div className="surface overflow-hidden">
      <div className="flex gap-4 border-b-2 border-edge bg-ground px-4 py-3">
        {CELL_WIDTHS.map((w, i) => (
          <Skeleton key={i} variant="text" width={w} height={16} className={i > 1 ? 'hidden sm:block' : undefined} />
        ))}
      </div>
      {times(rows).map((r) => (
        <div key={r} className="flex items-center gap-4 border-b-2 border-dashed border-line px-4 py-3.5 last:border-b-0">
          <div className="flex flex-col gap-1" style={{ width: CELL_WIDTHS[0] }}>
            <Skeleton variant="text" width={`${70 + ((r * 13) % 30)}%`} />
            <Skeleton variant="text" width="45%" height={14} />
          </div>
          {CELL_WIDTHS.slice(1).map((w, i) => (
            <Skeleton key={i} variant="text" width={w} className={i > 0 ? 'hidden sm:block' : undefined} />
          ))}
        </div>
      ))}
    </div>
  )
}

// Sin marco: normalmente va dentro de una Section.
function ChartSkeleton({ height = 280 }) {
  return <Skeleton variant="rounded" height={height} />
}

function DashboardSkeleton() {
  return (
    <div className="flex flex-col gap-8">
      <div className="grid grid-cols-2 gap-3 sm:gap-6 lg:grid-cols-4">
        {times(4).map((i) => (
          <div key={i} className="surface flex min-h-28 flex-col justify-between p-4 sm:min-h-36 sm:p-5">
            <Skeleton variant="text" width="55%" height={16} />
            <Skeleton variant="text" width="75%" height={44} />
          </div>
        ))}
      </div>
      <div className="surface p-5">
        <Skeleton variant="text" width={180} height={24} className="mb-3" />
        <ChartSkeleton />
      </div>
    </div>
  )
}

function FormSkeleton() {
  return (
    <div className="surface grid grid-cols-1 gap-4 p-5 sm:grid-cols-2">
      {times(6).map((i) => (
        <Skeleton key={i} variant="rounded" height={48} />
      ))}
    </div>
  )
}

function ListSkeleton({ rows }) {
  return (
    <div className="flex flex-col gap-3">
      {times(rows).map((i) => (
        <div key={i} className="flex items-center gap-3">
          <Skeleton variant="text" width={20} />
          <Skeleton variant="text" className="flex-1" />
          <Skeleton variant="text" width={64} />
        </div>
      ))}
    </div>
  )
}

// Encabezado + filtros + tabla: lo que se ve mientras llega el código de una página.
export function PageSkeleton() {
  return (
    <div aria-hidden="true">
      <Skeleton variant="text" width={220} height={48} />
      <Skeleton variant="text" width="60%" className="mb-8" />
      <div className="mb-6 flex flex-wrap gap-3">
        <Skeleton variant="rounded" width={220} height={44} />
        <Skeleton variant="rounded" width={160} height={44} />
      </div>
      <TableSkeleton rows={5} />
    </div>
  )
}

const VARIANTS = { table: TableSkeleton, chart: ChartSkeleton, dashboard: DashboardSkeleton, form: FormSkeleton, list: ListSkeleton, page: PageSkeleton }

// Esqueleto con la forma del contenido que viene (variant) y aviso de cold start de Render tras 5 s.
export function Loading({ label = 'Cargando…', rows = 5, variant = 'table' }) {
  const [slow, setSlow] = useState(false)
  useEffect(() => {
    const timer = setTimeout(() => setSlow(true), 5000)
    return () => clearTimeout(timer)
  }, [])
  const Shape = VARIANTS[variant] ?? TableSkeleton

  return (
    <div role="status" aria-live="polite" className="flex flex-col gap-4">
      <div aria-hidden="true">
        <Shape rows={rows} />
      </div>
      <p className={slow ? 'text-center text-sm text-ink-soft' : 'sr-only'}>
        {slow ? 'El servidor está despertando. La primera carga puede tardar hasta un minuto.' : label}
      </p>
    </div>
  )
}

// Pantalla completa mientras se verifica la sesión: barra lateral (o header en móvil) + página.
export function AppShellSkeleton() {
  return (
    <div role="status" aria-label="Verificando tu sesión" className="flex min-h-svh flex-col bg-ground md:flex-row">
      <div className="hidden w-64 shrink-0 flex-col gap-6 border-r-2 border-edge p-6 md:flex" aria-hidden="true">
        <Skeleton variant="rounded" height={56} />
        <Skeleton variant="rounded" height={52} />
        {times(7).map((i) => (
          <Skeleton key={i} variant="rounded" height={40} />
        ))}
      </div>
      <div className="flex items-center gap-3 border-b-2 border-edge px-3 py-2.5 md:hidden" aria-hidden="true">
        <Skeleton variant="rounded" width={40} height={40} />
        <Skeleton variant="text" width={120} height={32} />
        <Skeleton variant="rounded" width={120} height={36} className="ml-auto" />
      </div>
      <div className="mx-auto w-full max-w-6xl flex-1 px-4 py-7 sm:px-6 md:px-10 md:py-10">
        <PageSkeleton />
      </div>
    </div>
  )
}

export function Empty({ title, children, action, icon }) {
  return (
    <div className="surface-inset flex flex-col items-center gap-3 bg-panel px-6 py-12 text-center">
      <span className="grid h-12 w-12 place-items-center text-ink-soft opacity-70 [&_svg]:!text-5xl" aria-hidden="true">
        {icon ?? <InboxOutlinedIcon />}
      </span>
      <p className="font-display text-xl font-bold text-ink">{title}</p>
      {children && <div className="max-w-md text-sm text-ink-soft">{children}</div>}
      {action && <div className="mt-1">{action}</div>}
    </div>
  )
}

// Aviso descartable tras una acción: notice = { severity, text } o null.
export function Notice({ notice, onClose }) {
  if (!notice) return null
  return (
    <Alert severity={notice.severity} className="mb-4" onClose={onClose}>
      {notice.text}
    </Alert>
  )
}

export function ErrorView({ error, onRetry }) {
  return (
    <div
      role="alert"
      className="flex flex-col items-center gap-3 border-2 border-crit bg-crit-tint px-6 py-12 text-center [border-radius:var(--radius-sketch-sm)]"
    >
      <span className="grid h-12 w-12 place-items-center rounded-full bg-panel text-crit" aria-hidden="true">
        <ErrorOutlinedIcon />
      </span>
      <p className="font-display text-xl font-bold text-crit">No se pudo cargar</p>
      <p className="max-w-md text-sm text-ink">{error?.message || 'Ocurrió un error inesperado.'}</p>
      {onRetry && (
        <Button variant="outlined" color="error" onClick={onRetry} className="mt-1">
          Reintentar
        </Button>
      )}
    </div>
  )
}
