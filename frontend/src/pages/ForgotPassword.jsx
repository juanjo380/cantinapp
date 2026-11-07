import Alert from '@mui/material/Alert'
import Button from '@mui/material/Button'
import ArrowForwardIcon from '@mui/icons-material/ArrowForward'
import LockIcon from '@mui/icons-material/LockOutlined'
import MailIcon from '@mui/icons-material/MailOutlined'
import PinIcon from '@mui/icons-material/PinOutlined'
import { useEffect, useState } from 'react'
import { Link as RouterLink, useNavigate, useSearchParams } from 'react-router-dom'
import { authApi } from '../api/helper'
import { useAuth } from '../auth/context'
import AuthShell from '../components/auth/AuthShell'
import IconField, { PasswordField } from '../components/ui/IconField'

const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
const RESEND_SECONDS = 60 // = RESET_RESEND_SECONDS del backend

// Paso 1: correo -> el backend envía un código de 6 dígitos (vence en 5 min).
// Paso 2: código + nueva contraseña -> se cambia y se inicia sesión con ella.
export default function ForgotPassword() {
  const { login } = useAuth()
  const navigate = useNavigate()
  const [params] = useSearchParams()
  const [step, setStep] = useState('email')
  const [email, setEmail] = useState(params.get('email') ?? '')
  const [form, setForm] = useState({ code: '', password: '', confirm: '' })
  const [errors, setErrors] = useState({})
  const [notice, setNotice] = useState(null)
  const [loading, setLoading] = useState(false)
  const [wait, setWait] = useState(0)

  useEffect(() => {
    if (wait <= 0) return undefined
    const id = setTimeout(() => setWait((w) => w - 1), 1000)
    return () => clearTimeout(id)
  }, [wait])

  async function sendCode(event) {
    event?.preventDefault()
    if (!EMAIL_RE.test(email.trim())) {
      setErrors({ email: 'Escribe un correo válido.' })
      return
    }
    setErrors({})
    setNotice(null)
    setLoading(true)
    try {
      const res = await authApi.forgotPassword(email.trim())
      setNotice({ severity: 'info', text: res.detail })
      setStep('code')
      setWait(RESEND_SECONDS)
    } catch (err) {
      setNotice({ severity: 'error', text: err.message })
    } finally {
      setLoading(false)
    }
  }

  async function onReset(event) {
    event.preventDefault()
    const next = {}
    if (!/^\d{6}$/.test(form.code.trim())) next.code = 'El código tiene 6 números.'
    if (form.password.length < 8) next.password = 'Mínimo 8 caracteres.'
    if (form.confirm !== form.password) next.confirm = 'Las contraseñas no coinciden.'
    setErrors(next)
    if (Object.keys(next).length) return
    setNotice(null)
    setLoading(true)
    try {
      await authApi.resetPassword({ email: email.trim(), code: form.code.trim(), new_password: form.password })
      await login(email.trim(), form.password)
      navigate('/', { replace: true })
    } catch (err) {
      setNotice({ severity: 'error', text: err.message })
      setLoading(false)
    }
  }

  const field = (name) => ({
    value: form[name],
    onChange: (e) => setForm((f) => ({ ...f, [name]: e.target.value })),
    error: Boolean(errors[name]),
    helperText: errors[name],
    fullWidth: true,
  })

  return (
    <AuthShell
      title="Recupera tu contraseña"
      subtitle={
        step === 'email'
          ? 'Te enviamos un código a tu correo para crear una contraseña nueva.'
          : `Revisa ${email.trim()} (también la carpeta de spam).`
      }
      footer={
        <RouterLink to="/login" className="sketch-link">
          Volver a iniciar sesión
        </RouterLink>
      }
    >
      {notice && (
        <Alert severity={notice.severity} className="mb-4">
          {notice.text}
        </Alert>
      )}
      {step === 'email' ? (
        <form onSubmit={sendCode} noValidate className="flex flex-col gap-4">
          <IconField
            icon={<MailIcon fontSize="small" />}
            label="Correo de tu cuenta"
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            error={Boolean(errors.email)}
            helperText={errors.email}
            autoComplete="email"
            autoFocus
            fullWidth
          />
          <Button type="submit" variant="contained" size="large" disabled={loading} endIcon={<ArrowForwardIcon />}>
            {loading ? 'Enviando…' : 'Enviar código'}
          </Button>
        </form>
      ) : (
        <form onSubmit={onReset} noValidate className="flex flex-col gap-4">
          <IconField
            icon={<PinIcon fontSize="small" />}
            label="Código de 6 dígitos"
            autoComplete="one-time-code"
            slotProps={{ htmlInput: { maxLength: 6, inputMode: 'numeric' } }}
            autoFocus
            {...field('code')}
          />
          <PasswordField
            icon={<LockIcon fontSize="small" />}
            label="Nueva contraseña"
            autoComplete="new-password"
            {...field('password')}
          />
          <PasswordField
            icon={<LockIcon fontSize="small" />}
            label="Confirmar nueva contraseña"
            autoComplete="new-password"
            {...field('confirm')}
          />
          <Button type="submit" variant="contained" size="large" disabled={loading} endIcon={<ArrowForwardIcon />}>
            {loading ? 'Guardando…' : 'Cambiar y entrar'}
          </Button>
          <Button onClick={() => sendCode()} disabled={loading || wait > 0}>
            {wait > 0 ? `Pedir otro código en ${wait} s` : 'Pedir otro código'}
          </Button>
        </form>
      )}
    </AuthShell>
  )
}
