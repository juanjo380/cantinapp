import Button from '@mui/material/Button'
import Skeleton from '@mui/material/Skeleton'
import ErrorOutlinedIcon from '@mui/icons-material/ErrorOutlined'
import InboxOutlinedIcon from '@mui/icons-material/InboxOutlined'
import { useEffect, useState } from 'react'

export function Loading({ label = 'Cargando…', rows = 4 }) {
  const [slow, setSlow] = useState(false)
  useEffect(() => {
    const timer = setTimeout(() => setSlow(true), 5000)
    return () => clearTimeout(timer)
  }, [])

  return (
    <div role="status" aria-live="polite" className="flex flex-col gap-4 py-4">
      <div className="flex flex-col gap-3" aria-hidden="true">
        <Skeleton variant="rounded" height={40} />
        {Array.from({ length: rows }).map((_, index) => (
          <Skeleton key={index} variant="rounded" height={54} />
        ))}
      </div>
      <p className="text-center text-sm text-ink-soft">
        {slow
          ? 'El servidor está despertando. La primera carga puede tardar hasta un minuto.'
          : label}
      </p>
    </div>
  )
}

export function Empty({ title, children, action, icon }) {
  return (
    <div className="flex flex-col items-center gap-3 rounded-lg border border-dashed border-line bg-panel px-6 py-14 text-center">
      <span className="grid h-12 w-12 place-items-center rounded-full bg-ground text-ink-soft" aria-hidden="true">
        {icon ?? <InboxOutlinedIcon />}
      </span>
      <p className="text-lg font-semibold text-ink">{title}</p>
      {children && <div className="max-w-md text-sm text-ink-soft">{children}</div>}
      {action && <div className="mt-1">{action}</div>}
    </div>
  )
}

export function ErrorView({ error, onRetry }) {
  return (
    <div
      role="alert"
      className="flex flex-col items-center gap-3 rounded-lg border border-crit bg-crit-tint px-6 py-12 text-center"
    >
      <span className="grid h-12 w-12 place-items-center rounded-full bg-panel text-crit" aria-hidden="true">
        <ErrorOutlinedIcon />
      </span>
      <p className="text-lg font-semibold text-crit">No se pudo cargar</p>
      <p className="max-w-md text-sm text-ink">{error?.message || 'Ocurrió un error inesperado.'}</p>
      {onRetry && (
        <Button variant="outlined" color="error" onClick={onRetry} className="mt-1">
          Reintentar
        </Button>
      )}
    </div>
  )
}
