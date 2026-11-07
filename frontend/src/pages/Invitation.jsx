import Alert from '@mui/material/Alert'
import Button from '@mui/material/Button'
import ArrowForwardIcon from '@mui/icons-material/ArrowForward'
import PinIcon from '@mui/icons-material/PinOutlined'
import { useState } from 'react'
import { Link as RouterLink, useNavigate, useSearchParams } from 'react-router-dom'
import { businessApi } from '../api/helper'
import { useAuth } from '../auth/context'
import AuthShell from '../components/auth/AuthShell'
import IconField from '../components/ui/IconField'
import { Loading } from '../components/ui/States'
import { useApi } from '../hooks/useApi'
import { formatDateTime, ROLE_LABELS } from '../utils/format'

// Llega desde el enlace del correo (/invitacion?token=…). Exige la sesión de la cuenta invitada
// y el código de 6 dígitos que le dicta quien invitó.
export default function Invitation() {
  const { user, apply, setNeedsPick, logout } = useAuth()
  const navigate = useNavigate()
  const [params] = useSearchParams()
  const token = params.get('token') ?? ''
  const { data, loading, error } = useApi(() => businessApi.previewInvitation(token), [token])
  const [code, setCode] = useState('')
  const [codeError, setCodeError] = useState('')
  const [serverError, setServerError] = useState('')
  const [saving, setSaving] = useState(false)

  async function onAccept(event) {
    event.preventDefault()
    if (!/^\d{6}$/.test(code.trim())) {
      setCodeError('El código tiene 6 números.')
      return
    }
    setCodeError('')
    setServerError('')
    setSaving(true)
    try {
      apply(await businessApi.acceptInvitation({ token, code: code.trim() }))
      setNeedsPick(false)
      navigate('/', { replace: true })
    } catch (err) {
      setServerError(err.message)
      setSaving(false)
    }
  }

  async function switchAccount() {
    await logout()
    navigate('/login', { replace: true, state: { from: `/invitacion?token=${encodeURIComponent(token)}` } })
  }

  const footer = (
    <RouterLink to="/" className="sketch-link">
      Ir a mi negocio
    </RouterLink>
  )

  if (loading) {
    return (
      <AuthShell title="Invitación" subtitle="Revisando la invitación…" footer={footer}>
        <Loading variant="form" label="Revisando la invitación…" />
      </AuthShell>
    )
  }

  if (error) {
    return (
      <AuthShell title="Invitación" subtitle={`Tienes la sesión abierta como ${user.email}.`} footer={footer}>
        <Alert severity="error" className="mb-4">
          {error.message}
        </Alert>
        {error.status === 403 && (
          <Button variant="outlined" onClick={switchAccount} fullWidth>
            Entrar con otra cuenta
          </Button>
        )}
      </AuthShell>
    )
  }

  return (
    <AuthShell
      title={`Únete a «${data.business_name}»`}
      subtitle={`${data.invited_by_name} te invitó como ${(ROLE_LABELS[data.role] ?? data.role).toLowerCase()}.`}
      footer={footer}
    >
      <form onSubmit={onAccept} noValidate className="flex flex-col gap-4">
        {serverError && <Alert severity="error">{serverError}</Alert>}
        <p className="text-sm text-ink-soft">
          Escribe el código de seguridad que te dio <strong>{data.invited_by_name}</strong>. No viene en el correo: así
          confirmamos que eres la persona que quiso invitar. Vence el {formatDateTime(data.expires_at)}.
        </p>
        <IconField
          icon={<PinIcon fontSize="small" />}
          label="Código de seguridad"
          value={code}
          onChange={(e) => setCode(e.target.value)}
          error={Boolean(codeError)}
          helperText={codeError}
          slotProps={{ htmlInput: { maxLength: 6, inputMode: 'numeric' } }}
          autoComplete="off"
          autoFocus
          fullWidth
        />
        <Button type="submit" variant="contained" size="large" disabled={saving} endIcon={<ArrowForwardIcon />}>
          {saving ? 'Uniéndote…' : 'Aceptar invitación'}
        </Button>
      </form>
    </AuthShell>
  )
}
