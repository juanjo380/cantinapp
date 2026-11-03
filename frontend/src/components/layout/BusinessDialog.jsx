import AddBusinessIcon from '@mui/icons-material/AddBusinessOutlined'
import CheckIcon from '@mui/icons-material/Check'
import StorefrontIcon from '@mui/icons-material/StorefrontOutlined'
import Button from '@mui/material/Button'
import TextField from '@mui/material/TextField'
import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../../auth/context'
import { ROLE_LABELS } from '../../utils/format'
import FormDialog from '../ui/FormDialog'
import { Stamp } from '../ui/Stamp'

// Elegir el negocio activo o crear uno nuevo. Cambiar de negocio emite un token nuevo y vuelve al dashboard.
export default function BusinessDialog({ onClose }) {
  const { session, switchBusiness, createBusiness } = useAuth()
  const navigate = useNavigate()
  const [creating, setCreating] = useState(!session?.businesses?.length)
  const [name, setName] = useState('')
  const [busy, setBusy] = useState(null)
  const [error, setError] = useState('')

  async function run(key, action) {
    setBusy(key)
    setError('')
    try {
      await action()
      onClose()
      navigate('/', { replace: true })
    } catch (err) {
      setError(err.message)
    } finally {
      setBusy(null)
    }
  }

  function onCreate() {
    if (!name.trim()) {
      setError('Escribe el nombre del nuevo negocio.')
      return
    }
    run('new', () => createBusiness(name.trim()))
  }

  return (
    <FormDialog
      title={session?.businesses?.length ? 'Elige tu negocio' : 'Crea tu negocio'}
      icon={<StorefrontIcon />}
      onClose={onClose}
      error={error}
    >
      {session?.businesses?.length > 0 && (
        <ul className="flex flex-col gap-2" aria-label="Tus negocios">
          {session.businesses.map((b) => {
            const active = b.business_id === session.business_id
            return (
              <li key={b.business_id}>
                <button
                  type="button"
                  disabled={busy !== null}
                  aria-current={active ? 'true' : undefined}
                  onClick={() => (active ? onClose() : run(b.business_id, () => switchBusiness(b.business_id)))}
                  className={`flex w-full cursor-pointer items-center gap-3 px-4 py-3 text-left transition-colors ${
                    active ? 'surface border-edge bg-brand-tint' : 'surface-inset hover:bg-brand-tint'
                  }`}
                >
                  <span className="min-w-0 flex-1">
                    <span className="block truncate font-bold text-ink">{b.business_name}</span>
                    <span className="text-xs text-ink-soft">{ROLE_LABELS[b.role] ?? b.role}</span>
                  </span>
                  {busy === b.business_id && <span className="text-xs text-ink-soft">Cambiando…</span>}
                  {active && <CheckIcon fontSize="small" className="text-brand-ink" titleAccess="Negocio activo" />}
                  {!b.profile_completed && <Stamp tone="warn">Perfil incompleto</Stamp>}
                </button>
              </li>
            )
          })}
        </ul>
      )}

      {creating ? (
        <div className="flex flex-col gap-3 border-t-2 border-dashed border-line pt-4">
          <TextField
            label="Nombre del nuevo negocio"
            value={name}
            onChange={(e) => setName(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && onCreate()}
            fullWidth
            autoFocus
          />
          <p className="text-xs text-ink-soft">Serás su dueño. Cada negocio tiene su propio inventario y ventas.</p>
          <Button variant="contained" startIcon={<AddBusinessIcon />} onClick={onCreate} disabled={busy !== null}>
            {busy === 'new' ? 'Creando…' : 'Crear negocio'}
          </Button>
        </div>
      ) : (
        <Button variant="outlined" startIcon={<AddBusinessIcon />} onClick={() => setCreating(true)} className="self-start">
          Crear otro negocio
        </Button>
      )}
    </FormDialog>
  )
}
