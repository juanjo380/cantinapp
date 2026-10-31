import Alert from '@mui/material/Alert'
import Button from '@mui/material/Button'
import ArrowForwardIcon from '@mui/icons-material/ArrowForward'
import LockIcon from '@mui/icons-material/LockOutlined'
import MailIcon from '@mui/icons-material/MailOutlined'
import { useState } from 'react'
import { Link as RouterLink, useLocation, useNavigate } from 'react-router-dom'
import { useAuth } from '../auth/context'
import AuthShell from '../components/auth/AuthShell'
import IconField, { PasswordField } from '../components/ui/IconField'

export default function Login() {
  const { login } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [errors, setErrors] = useState({})
  const [serverError, setServerError] = useState('')
  const [loading, setLoading] = useState(false)

  async function onSubmit(event) {
    event.preventDefault()
    const next = {}
    if (!email.trim()) next.email = 'Escribe tu correo.'
    else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) next.email = 'Correo no válido.'
    if (!password) next.password = 'Escribe tu contraseña.'
    setErrors(next)
    if (Object.keys(next).length) return

    setServerError('')
    setLoading(true)
    try {
      await login(email.trim(), password)
      navigate(location.state?.from || '/', { replace: true })
    } catch (err) {
      setServerError(err.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <AuthShell
      title="Entra a tu negocio"
      subtitle="Tu inventario y tus recomendaciones, listos para decidir."
      footer={
        <>
          ¿No tienes cuenta?{' '}
          <RouterLink to="/registro" className="sketch-link">
            Crea tu negocio
          </RouterLink>
        </>
      }
    >
      <form onSubmit={onSubmit} noValidate className="flex flex-col gap-4">
        {serverError && <Alert severity="error">{serverError}</Alert>}
        <IconField
          icon={<MailIcon fontSize="small" />}
          label="Correo"
          type="email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          error={Boolean(errors.email)}
          helperText={errors.email}
          autoComplete="email"
          fullWidth
        />
        <PasswordField
          icon={<LockIcon fontSize="small" />}
          label="Contraseña"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          error={Boolean(errors.password)}
          helperText={errors.password}
          autoComplete="current-password"
          fullWidth
        />
        <Button type="submit" variant="contained" size="large" disabled={loading} endIcon={<ArrowForwardIcon />}>
          {loading ? 'Entrando…' : 'Entrar'}
        </Button>
      </form>
    </AuthShell>
  )
}
