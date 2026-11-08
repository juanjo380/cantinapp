import ScienceOutlinedIcon from '@mui/icons-material/ScienceOutlined'
import Alert from '@mui/material/Alert'
import Button from '@mui/material/Button'
import { useState } from 'react'
import { demoApi } from '../../api/helper'
import { useAuth } from '../../auth/context'
import { useApi } from '../../hooks/useApi'

// Datos de ejemplo (GET/POST/DELETE /api/demo). Si hay datos de ejemplo muestra un aviso para
// borrarlos; si el negocio está vacío y quien mira es el dueño, el botón para cargarlos.
// `onChange` se llama tras cargar o borrar para que la página recargue lo suyo; `noticeOnly` nunca
// ofrece cargar (p. ej. dentro del diálogo de CSV, donde solo sirve el aviso).
export default function DemoData({ onChange, noticeOnly = false }) {
  const { session } = useAuth()
  const status = useApi(() => demoApi.status(), [])
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const isOwner = session?.role === 'OWNER'

  async function run(action) {
    setBusy(true)
    setError('')
    try {
      await action()
      status.reload()
      onChange?.()
    } catch (err) {
      setError(err.message)
    } finally {
      setBusy(false)
    }
  }

  const data = status.data
  if (!data) return null

  if (data.has_demo) {
    return (
      <Alert
        severity="info"
        icon={<ScienceOutlinedIcon />}
        action={
          isOwner && (
            <Button color="inherit" size="small" disabled={busy} onClick={() => run(demoApi.remove)}>
              {busy ? 'Borrando…' : 'Borrar datos de ejemplo'}
            </Button>
          )
        }
      >
        Estás viendo datos de ejemplo (productos marcados «(ejemplo)»). Bórralos antes de cargar tus ventas reales
        para que no se mezclen.
        {error && <span className="block font-semibold">{error}</span>}
      </Alert>
    )
  }

  if (noticeOnly || !data.can_load) return null
  return (
    <div className="flex flex-col items-center gap-2">
      <Button variant="outlined" startIcon={<ScienceOutlinedIcon />} disabled={busy} onClick={() => run(demoApi.load)}>
        {busy ? 'Cargando ejemplo…' : 'Cargar datos de ejemplo'}
      </Button>
      <p className="max-w-md text-center text-xs text-ink-soft">
        12 productos de cantina y 90 días de ventas para ver predicciones, alertas y recomendaciones ya mismo. Los
        borras con un clic.
      </p>
      {error && <p className="text-xs font-semibold text-crit">{error}</p>}
    </div>
  )
}
