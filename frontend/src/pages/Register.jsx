import Alert from '@mui/material/Alert'
import Button from '@mui/material/Button'
import Checkbox from '@mui/material/Checkbox'
import FormControlLabel from '@mui/material/FormControlLabel'
import ArrowForwardIcon from '@mui/icons-material/ArrowForward'
import LockIcon from '@mui/icons-material/LockOutlined'
import MailIcon from '@mui/icons-material/MailOutlined'
import StoreIcon from '@mui/icons-material/StorefrontOutlined'
import { useState } from 'react'
import { Link as RouterLink, useNavigate } from 'react-router-dom'
import { useAuth } from '../auth/context'
import AuthShell from '../components/auth/AuthShell'
import LegalDialog from '../components/auth/LegalDialog'
import IconField, { PasswordField } from '../components/ui/IconField'

// [clave, texto antes, texto del enlace, texto después, obligatorio]. Cortos para que cada uno quepa en una línea.
const CONSENTS = [
  ['terms', 'Acepto los', 'Términos y condiciones', '', true],
  ['privacy', 'Acepto la', 'Política de privacidad y cookies', '', true],
  ['ml', 'Autorizo el', 'uso anónimo de mis datos', ' para predicciones (opcional)', false],
]

export default function Register() {
  const { register } = useAuth()
  const navigate = useNavigate()
  const [form, setForm] = useState({ business_name: '', email: '', password: '', confirm: '' })
  const [consent, setConsent] = useState({ terms: false, privacy: false, ml: false })
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
      next.consent = 'Debes aceptar los términos y la política de privacidad y cookies.'
    setErrors(next)
    if (Object.keys(next).length) return

    setServerError('')
    setLoading(true)
    try {
      // El nombre del usuario se pide después, en la personalización del perfil.
      await register({
        business_name: form.business_name.trim(),
        email: form.email.trim(),
        password: form.password,
        accept_terms: consent.terms,
        accept_privacy: consent.privacy,
        allow_ml_data: consent.ml,
      })
      navigate('/', { replace: true, state: { onboarding: true } }) // AppLayout muestra la bienvenida
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
      wide
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
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
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
        </div>
        <fieldset className="flex flex-col">
          <legend className="sr-only">Términos y autorizaciones</legend>
          {CONSENTS.map(([key, before, link, after, required]) => (
            <FormControlLabel
              key={key}
              control={
                <Checkbox
                  size="small"
                  checked={consent[key]}
                  // Sin `required`: MUI añadiría su propio asterisco en otra línea; se marca a mano abajo.
                  slotProps={{ input: { 'aria-required': required || undefined } }}
                  onChange={(e) => setConsent((c) => ({ ...c, [key]: e.target.checked }))}
                />
              }
              label={
                <span>
                  {before}{' '}
                  <button
                    type="button"
                    className="sketch-link inline cursor-pointer"
                    onClick={(e) => {
                      e.preventDefault() // abrir el documento no debe marcar la casilla
                      setLegal(key)
                    }}
                  >
                    {link}
                  </button>
                  {after}
                  {required && (
                    <span className="text-crit" aria-hidden="true">
                      {' '}*
                    </span>
                  )}
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
        <Button type="submit" variant="contained" disabled={loading} endIcon={<ArrowForwardIcon />}>
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
