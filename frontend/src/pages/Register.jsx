import Alert from '@mui/material/Alert'
import Button from '@mui/material/Button'
import TextField from '@mui/material/TextField'
import { useState } from 'react'
import { Link as RouterLink, useNavigate } from 'react-router-dom'
import { useAuth } from '../auth/context'
import AuthShell from '../components/auth/AuthShell'

export default function Register() {
  const { register } = useAuth()
  const navigate = useNavigate()
  const [form, setForm] = useState({ business_name: '', full_name: '', email: '', password: '' })
  const [errors, setErrors] = useState({})
  const [serverError, setServerError] = useState('')
  const [loading, setLoading] = useState(false)

  const set = (field) => (event) => setForm((f) => ({ ...f, [field]: event.target.value }))

  async function onSubmit(event) {
    event.preventDefault()
    const next = {}
    if (!form.business_name.trim()) next.business_name = 'Escribe el nombre de tu negocio.'
    if (!form.email.trim()) next.email = 'Escribe tu correo.'
    else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(form.email)) next.email = 'Correo no válido.'
    if (form.password.length < 8) next.password = 'La contraseña debe tener 8 caracteres o más.'
    setErrors(next)
    if (Object.keys(next).length) return

    setServerError('')
    setLoading(true)
    try {
      await register({
        business_name: form.business_name.trim(),
        full_name: form.full_name.trim() || undefined,
        email: form.email.trim(),
        password: form.password,
      })
      navigate('/', { replace: true })
    } catch (err) {
      setServerError(
        err.status === 409 ? 'Ese correo ya está registrado. Inicia sesión.' : err.message,
      )
    } finally {
      setLoading(false)
    }
  }

  return (
    <AuthShell
      title="Crea tu negocio"
      subtitle="Empieza a controlar tu inventario y tus compras."
      footer={
        <>
          ¿Ya tienes cuenta?{' '}
          <RouterLink to="/login" className="font-semibold text-brand underline underline-offset-2">
            Inicia sesión
          </RouterLink>
        </>
      }
    >
      <form onSubmit={onSubmit} noValidate className="flex flex-col gap-4">
        {serverError && <Alert severity="error">{serverError}</Alert>}
        <TextField
          label="Nombre del negocio"
          value={form.business_name}
          onChange={set('business_name')}
          error={Boolean(errors.business_name)}
          helperText={errors.business_name}
          autoComplete="organization"
          fullWidth
        />
        <TextField
          label="Tu nombre (opcional)"
          value={form.full_name}
          onChange={set('full_name')}
          autoComplete="name"
          fullWidth
        />
        <TextField
          label="Correo"
          type="email"
          value={form.email}
          onChange={set('email')}
          error={Boolean(errors.email)}
          helperText={errors.email}
          autoComplete="email"
          fullWidth
        />
        <TextField
          label="Contraseña"
          type="password"
          value={form.password}
          onChange={set('password')}
          error={Boolean(errors.password)}
          helperText={errors.password || 'Mínimo 8 caracteres.'}
          autoComplete="new-password"
          fullWidth
        />
        <Button type="submit" variant="contained" size="large" disabled={loading}>
          {loading ? 'Creando…' : 'Crear cuenta'}
        </Button>
      </form>
    </AuthShell>
  )
}
