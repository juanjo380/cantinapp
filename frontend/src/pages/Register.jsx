import Alert from '@mui/material/Alert'
import Button from '@mui/material/Button'
import Checkbox from '@mui/material/Checkbox'
import FormControlLabel from '@mui/material/FormControlLabel'
import ArrowForwardIcon from '@mui/icons-material/ArrowForward'
import LockIcon from '@mui/icons-material/LockOutlined'
import MailIcon from '@mui/icons-material/MailOutlined'
import PersonIcon from '@mui/icons-material/PersonOutlined'
import StoreIcon from '@mui/icons-material/StorefrontOutlined'
import { useState } from 'react'
import { Link as RouterLink, useNavigate } from 'react-router-dom'
import { useAuth } from '../auth/context'
import AuthShell from '../components/auth/AuthShell'
import LegalDialog from '../components/auth/LegalDialog'
import IconField, { PasswordField } from '../components/ui/IconField'

// [clave, texto antes, texto del enlace, texto después, obligatorio]
const CONSENTS = [
  ['terms', 'Acepto los', 'Términos y condiciones', '', true],
  ['privacy', 'Autorizo el tratamiento de mis datos según la', 'Política de privacidad', '', true],
  ['cookies', 'He leído la', 'Política de cookies', '', true],
  ['ml', 'Autorizo el', 'uso anónimo de los datos de mi negocio', ' para mejorar las predicciones (opcional)', false],
]

export default function Register() {
  const { register } = useAuth()
  const navigate = useNavigate()
  const [form, setForm] = useState({ business_name: '', full_name: '', email: '', password: '', confirm: '' })
  const [consent, setConsent] = useState({ terms: false, privacy: false, cookies: false, ml: false })
  const [legal, setLegal] = useState(null)
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
    if (form.confirm !== form.password) next.confirm = 'Las contraseñas no coinciden.'
    if (CONSENTS.some(([key, , , , required]) => required && !consent[key]))
      next.consent = 'Debes aceptar los términos, la política de privacidad y la de cookies.'
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
        accept_terms: consent.terms,
        accept_privacy: consent.privacy,
        accept_cookies: consent.cookies,
        allow_ml_data: consent.ml,
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
          <RouterLink to="/login" className="sketch-link">
            Inicia sesión
          </RouterLink>
        </>
      }
    >
      <form onSubmit={onSubmit} noValidate className="flex flex-col gap-4">
        {serverError && <Alert severity="error">{serverError}</Alert>}
        <IconField
          icon={<StoreIcon fontSize="small" />}
          label="Nombre del negocio"
          value={form.business_name}
          onChange={set('business_name')}
          error={Boolean(errors.business_name)}
          helperText={errors.business_name}
          autoComplete="organization"
          fullWidth
        />
        <IconField
          icon={<PersonIcon fontSize="small" />}
          label="Tu nombre (opcional)"
          value={form.full_name}
          onChange={set('full_name')}
          autoComplete="name"
          fullWidth
        />
        <IconField
          icon={<MailIcon fontSize="small" />}
          label="Correo"
          type="email"
          value={form.email}
          onChange={set('email')}
          error={Boolean(errors.email)}
          helperText={errors.email}
          autoComplete="email"
          fullWidth
        />
        <PasswordField
          icon={<LockIcon fontSize="small" />}
          label="Contraseña"
          value={form.password}
          onChange={set('password')}
          error={Boolean(errors.password)}
          helperText={errors.password || 'Mínimo 8 caracteres.'}
          autoComplete="new-password"
          fullWidth
        />
        <PasswordField
          icon={<LockIcon fontSize="small" />}
          label="Confirmar contraseña"
          value={form.confirm}
          onChange={set('confirm')}
          error={Boolean(errors.confirm)}
          helperText={errors.confirm}
          autoComplete="new-password"
          fullWidth
        />
        <fieldset className="flex flex-col gap-1">
          <legend className="sr-only">Términos y autorizaciones</legend>
          {CONSENTS.map(([key, before, link, after, required]) => (
            <FormControlLabel
              key={key}
              className="items-start"
              control={
                <Checkbox
                  checked={consent[key]}
                  required={required}
                  onChange={(e) => setConsent((c) => ({ ...c, [key]: e.target.checked }))}
                />
              }
              label={
                <span className="mt-2 block">
                  {before}{' '}
                  <button
                    type="button"
                    className="sketch-link cursor-pointer"
                    onClick={(e) => {
                      e.preventDefault() // abrir el documento no debe marcar la casilla
                      setLegal(key)
                    }}
                  >
                    {link}
                  </button>
                  {after}
                </span>
              }
            />
          ))}
          {errors.consent && (
            <p role="alert" className="text-xs font-medium text-crit">
              {errors.consent}
            </p>
          )}
        </fieldset>
        <Button type="submit" variant="contained" size="large" disabled={loading} endIcon={<ArrowForwardIcon />}>
          {loading ? 'Creando…' : 'Crear cuenta'}
        </Button>
      </form>
      {legal && (
        <LegalDialog
          doc={legal}
          onClose={() => setLegal(null)}
          onAccept={() => {
            setConsent((c) => ({ ...c, [legal]: true }))
            setLegal(null)
          }}
        />
      )}
    </AuthShell>
  )
}
