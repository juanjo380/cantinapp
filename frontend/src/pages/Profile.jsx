import AddIcon from '@mui/icons-material/Add'
import DeleteOutlineIcon from '@mui/icons-material/DeleteOutlined'
import EditOutlinedIcon from '@mui/icons-material/EditOutlined'
import GroupAddIcon from '@mui/icons-material/GroupAddOutlined'
import MarkEmailReadIcon from '@mui/icons-material/MarkEmailReadOutlined'
import LogoutIcon from '@mui/icons-material/Logout'
import PlaceIcon from '@mui/icons-material/PlaceOutlined'
import Alert from '@mui/material/Alert'
import Button from '@mui/material/Button'
import FormControlLabel from '@mui/material/FormControlLabel'
import Switch from '@mui/material/Switch'
import Tab from '@mui/material/Tab'
import Tabs from '@mui/material/Tabs'
import TextField from '@mui/material/TextField'
import { useState } from 'react'
import { Link as RouterLink, useSearchParams } from 'react-router-dom'
import { authApi, businessApi } from '../api/helper'
import { useAuth } from '../auth/context'
import { PasswordField } from '../components/ui/IconField'
import DataTable, { RowAction, RowActions } from '../components/ui/DataTable'
import FormDialog from '../components/ui/FormDialog'
import PageHeader from '../components/ui/PageHeader'
import Section from '../components/ui/Section'
import SelectField from '../components/ui/SelectField'
import { Stamp } from '../components/ui/Stamp'
import { Empty, ErrorView, Loading, Notice } from '../components/ui/States'
import { useApi } from '../hooks/useApi'
import { formatDate, formatDateTime, ROLE_LABELS } from '../utils/format'

const TABS = [
  ['yo', 'Mi perfil'],
  ['negocio', 'Negocio'],
  ['sedes', 'Sedes'],
  ['equipo', 'Equipo'],
]
// Deben coincidir con BUSINESS_TYPES de backend/app/modules/business/domain/entities.py.
const BUSINESS_TYPES = [
  ['', 'Sin definir'],
  ['TIENDA', 'Tienda de barrio'],
  ['MINIMERCADO', 'Minimercado'],
  ['CANTINA_ESCOLAR', 'Cantina escolar'],
  ['CAFETERIA', 'Cafetería'],
  ['RESTAURANTE', 'Restaurante'],
  ['PANADERIA', 'Panadería'],
  ['DROGUERIA', 'Droguería'],
  ['OTRO', 'Otro'],
]
const DEPARTMENTS = [
  'Amazonas', 'Antioquia', 'Arauca', 'Atlántico', 'Bogotá D.C.', 'Bolívar', 'Boyacá', 'Caldas', 'Caquetá',
  'Casanare', 'Cauca', 'Cesar', 'Chocó', 'Córdoba', 'Cundinamarca', 'Guainía', 'Guaviare', 'Huila', 'La Guajira',
  'Magdalena', 'Meta', 'Nariño', 'Norte de Santander', 'Putumayo', 'Quindío', 'Risaralda',
  'San Andrés y Providencia', 'Santander', 'Sucre', 'Tolima', 'Valle del Cauca', 'Vaupés', 'Vichada',
]
const ROLE_OPTIONS = [
  ['MEMBER', 'Miembro: usa la app'],
  ['ADMIN', 'Administrador: además edita el negocio y el equipo'],
]
const PHONE_RE = /^\+?[\d\s()-]{7,20}$/
const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
const NIT_RE = /^[\d.\s]{6,20}(-\d)?$/

// Props de un TextField controlado: valor, cambio y error de validación.
function binder(form, setForm, errors) {
  return (name) => ({
    value: form[name],
    onChange: (event) => setForm((f) => ({ ...f, [name]: event.target.value })),
    error: Boolean(errors[name]),
    helperText: errors[name],
    fullWidth: true,
  })
}

// '' -> null para que el backend borre el campo en vez de guardar texto vacío.
const toPayload = (form) => Object.fromEntries(Object.entries(form).map(([k, v]) => [k, v.trim() === '' ? null : v.trim()]))

export default function Profile() {
  const { session } = useAuth()
  const [params, setParams] = useSearchParams()
  const tab = TABS.some(([key]) => key === params.get('tab')) ? params.get('tab') : 'yo'

  return (
    <>
      <PageHeader title="Perfil" subtitle="Tus datos, los de tu negocio, sus sedes y tu equipo." />

      {!session.profile_completed && (
        <Alert severity="info" className="mb-6">
          Para completar el perfil llena tu <strong>nombre</strong> en «Mi perfil» y, en «Negocio», el tipo, teléfono,
          dirección, departamento y ciudad (marcados con *).
        </Alert>
      )}

      <Tabs
        value={tab}
        onChange={(_, next) => setParams({ tab: next }, { replace: true })}
        variant="scrollable"
        allowScrollButtonsMobile
        className="mb-6 border-b border-line"
        aria-label="Secciones del perfil"
      >
        {TABS.map(([key, label]) => (
          <Tab key={key} value={key} label={label} />
        ))}
      </Tabs>

      {tab === 'yo' && <MyProfileTab />}
      {tab === 'negocio' && <BusinessTab />}
      {tab === 'sedes' && <LocationsTab />}
      {tab === 'equipo' && <TeamTab />}
    </>
  )
}

// --- Mi perfil -----------------------------------------------------------------

function MyProfileTab() {
  const { user, apply } = useAuth()
  const [form, setForm] = useState({
    full_name: user.full_name ?? '',
    job_title: user.job_title ?? '',
    phone: user.phone ?? '',
  })
  const [errors, setErrors] = useState({})
  const [notice, setNotice] = useState(null)
  const [saving, setSaving] = useState(false)
  const field = binder(form, setForm, errors)

  async function onSave(event) {
    event.preventDefault()
    const next = {}
    if (!form.full_name.trim()) next.full_name = 'Escribe tu nombre.'
    if (form.phone.trim() && !PHONE_RE.test(form.phone.trim())) next.phone = 'Teléfono no válido.'
    setErrors(next)
    if (Object.keys(next).length) return
    setSaving(true)
    setNotice(null)
    try {
      apply(await authApi.updateMe(toPayload(form)))
      setNotice({ severity: 'success', text: 'Tus datos quedaron guardados.' })
    } catch (err) {
      setNotice({ severity: 'error', text: err.message })
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
      <Section title="Mis datos">
        <Notice notice={notice} onClose={() => setNotice(null)} />
        <form onSubmit={onSave} noValidate className="flex flex-col gap-4">
          <TextField label="Nombre completo" required autoComplete="name" {...field('full_name')} />
          <TextField label="Cargo" placeholder="Ej.: Administradora" {...field('job_title')} />
          <TextField label="Teléfono" type="tel" autoComplete="tel" {...field('phone')} />
          <TextField label="Correo" value={user.email} disabled fullWidth helperText="Es tu usuario para entrar; no se puede cambiar." />
          <Button type="submit" variant="contained" disabled={saving} className="self-start">
            {saving ? 'Guardando…' : 'Guardar mis datos'}
          </Button>
        </form>
      </Section>
      <PasswordSection />
    </div>
  )
}

function PasswordSection() {
  const { user, apply } = useAuth()
  const [form, setForm] = useState({ current: '', next: '', confirm: '' })
  const [errors, setErrors] = useState({})
  const [notice, setNotice] = useState(null)
  const [saving, setSaving] = useState(false)
  const field = binder(form, setForm, errors)

  async function onSave(event) {
    event.preventDefault()
    const next = {}
    if (!form.current) next.current = 'Escribe tu contraseña actual.'
    if (form.next.length < 8) next.next = 'Mínimo 8 caracteres.'
    if (form.confirm !== form.next) next.confirm = 'Las contraseñas no coinciden.'
    setErrors(next)
    if (Object.keys(next).length) return
    setSaving(true)
    setNotice(null)
    try {
      // El backend cierra las demás sesiones y devuelve un token nuevo para esta.
      apply(await authApi.changePassword({ current_password: form.current, new_password: form.next }))
      setForm({ current: '', next: '', confirm: '' })
      setNotice({ severity: 'success', text: 'Contraseña actualizada. Cerramos tus sesiones en otros dispositivos.' })
    } catch (err) {
      setNotice({ severity: 'error', text: err.message })
    } finally {
      setSaving(false)
    }
  }

  return (
    <Section title="Cambiar contraseña">
      <Notice notice={notice} onClose={() => setNotice(null)} />
      <form onSubmit={onSave} noValidate className="flex flex-col gap-4">
        <PasswordField label="Contraseña actual" autoComplete="current-password" {...field('current')} />
        <RouterLink
          to={`/recuperar?email=${encodeURIComponent(user.email)}`}
          className="sketch-link -mt-2 self-start text-sm"
        >
          ¿No la recuerdas? Recibe un código por correo
        </RouterLink>
        <PasswordField label="Nueva contraseña" autoComplete="new-password" {...field('next')} />
        <PasswordField label="Confirmar nueva contraseña" autoComplete="new-password" {...field('confirm')} />
        <Button type="submit" variant="outlined" disabled={saving} className="self-start">
          {saving ? 'Actualizando…' : 'Cambiar contraseña'}
        </Button>
      </form>
    </Section>
  )
}

// --- Negocio -------------------------------------------------------------------

const BUSINESS_FIELDS = ['name', 'legal_name', 'tax_id', 'business_type', 'phone', 'email', 'address', 'city', 'department']

function BusinessTab() {
  const { data, loading, error, reload } = useApi(() => businessApi.get(), [])
  if (loading) return <Loading variant="form" label="Cargando tu negocio…" />
  if (error) return <ErrorView error={error} onRetry={reload} />
  return <BusinessForm initial={data} />
}

function BusinessForm({ initial }) {
  const { isAdmin, refresh } = useAuth()
  const [form, setForm] = useState(() => Object.fromEntries(BUSINESS_FIELDS.map((f) => [f, initial[f] ?? ''])))
  const [errors, setErrors] = useState({})
  const [notice, setNotice] = useState(null)
  const [saving, setSaving] = useState(false)
  const bind = binder(form, setForm, errors)
  const field = (name) => ({ ...bind(name), disabled: !isAdmin })

  async function onSave(event) {
    event.preventDefault()
    const v = toPayload(form)
    const next = {}
    if (!v.name) next.name = 'El negocio necesita un nombre.'
    if (v.tax_id && !NIT_RE.test(v.tax_id)) next.tax_id = 'Usa solo números y, si quieres, el dígito: 900123456-8.'
    if (v.phone && !PHONE_RE.test(v.phone)) next.phone = 'Teléfono no válido.'
    if (v.email && !EMAIL_RE.test(v.email)) next.email = 'Correo no válido.'
    setErrors(next)
    if (Object.keys(next).length) return
    setSaving(true)
    setNotice(null)
    try {
      const saved = await businessApi.update(v)
      setForm(Object.fromEntries(BUSINESS_FIELDS.map((f) => [f, saved[f] ?? ''])))
      await refresh() // nombre del negocio y estado del perfil en la barra lateral
      setNotice({ severity: 'success', text: 'Los datos del negocio quedaron guardados.' })
    } catch (err) {
      setNotice({ severity: 'error', text: err.message })
    } finally {
      setSaving(false)
    }
  }

  return (
    <form onSubmit={onSave} noValidate className="flex flex-col gap-6">
      {!isAdmin && (
        <Alert severity="info">Solo el dueño o un administrador puede editar los datos del negocio.</Alert>
      )}
      <Notice notice={notice} onClose={() => setNotice(null)} />
      <Section title="Datos del negocio">
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
          <TextField label="Nombre comercial" required {...field('name')} />
          <TextField label="Razón social" placeholder="Como aparece en el RUT" {...field('legal_name')} />
          <TextField
            label="NIT"
            placeholder="900123456-8"
            {...field('tax_id')}
            helperText={errors.tax_id || 'Con el dígito de verificación lo validamos.'}
          />
          <SelectField
            label="Tipo de negocio"
            required
            options={BUSINESS_TYPES}
            {...field('business_type')}
            onChange={(value) => setForm((f) => ({ ...f, business_type: value }))}
          />
        </div>
      </Section>
      <Section title="Contacto y ubicación">
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
          <TextField label="Teléfono" type="tel" required {...field('phone')} />
          <TextField label="Correo del negocio" type="email" {...field('email')} />
          <TextField label="Dirección" required className="sm:col-span-2" {...field('address')} />
          <SelectField
            label="Departamento"
            required
            options={[['', 'Elige un departamento'], ...DEPARTMENTS.map((d) => [d, d])]}
            {...field('department')}
            onChange={(value) => setForm((f) => ({ ...f, department: value }))}
          />
          <TextField label="Ciudad o municipio" required {...field('city')} />
        </div>
      </Section>
      {isAdmin && (
        <div className="flex flex-wrap items-center gap-3">
          <Button type="submit" variant="contained" disabled={saving}>
            {saving ? 'Guardando…' : 'Guardar negocio'}
          </Button>
          <span className="text-xs text-ink-soft">* Necesarios para completar el perfil.</span>
        </div>
      )}
    </form>
  )
}

// --- Sedes ---------------------------------------------------------------------

function LocationsTab() {
  const { isAdmin } = useAuth()
  const { data, loading, error, reload } = useApi(() => businessApi.locations(), [])
  const [editing, setEditing] = useState(null) // 'new' | sede
  const [notice, setNotice] = useState(null)

  async function onDelete(location) {
    if (!window.confirm(`¿Eliminar la sede "${location.name}"?`)) return
    setNotice(null)
    try {
      await businessApi.removeLocation(location.id)
      reload()
    } catch (err) {
      setNotice({ severity: 'error', text: err.message })
    }
  }

  const columns = [
    {
      key: 'name',
      header: 'Sede',
      render: (l) => (
        <span className="flex flex-wrap items-center gap-2 font-medium text-ink">
          {l.name}
          {l.is_main && <Stamp tone="ok">Principal</Stamp>}
        </span>
      ),
    },
    { key: 'address', header: 'Dirección', render: (l) => [l.address, l.city].filter(Boolean).join(', ') || '—' },
    { key: 'phone', header: 'Teléfono', hideOnMobile: true, render: (l) => l.phone || '—' },
    ...(isAdmin
      ? [
          {
            key: 'actions',
            header: 'Acciones',
            align: 'right',
            render: (l) => (
              <RowActions
                actions={[
                  { title: 'Editar', icon: <EditOutlinedIcon fontSize="small" />, onClick: () => setEditing(l) },
                  { title: 'Eliminar', color: 'error', icon: <DeleteOutlineIcon fontSize="small" />, onClick: () => onDelete(l) },
                ]}
              />
            ),
          },
        ]
      : []),
  ]

  return (
    <>
      <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
        <p className="max-w-xl text-sm text-ink-soft">
          Registra los puntos de venta de tu negocio. Por ahora el inventario y las ventas son del negocio completo.
        </p>
        {isAdmin && (
          <Button variant="contained" startIcon={<AddIcon />} onClick={() => setEditing('new')}>
            Nueva sede
          </Button>
        )}
      </div>
      <Notice notice={notice} onClose={() => setNotice(null)} />
      <DataTable
        label="Sedes"
        columns={columns}
        rows={data}
        loading={loading}
        error={error}
        onRetry={reload}
        empty={
          <Empty icon={<PlaceIcon />} title="Aún no tienes sedes">
            {isAdmin ? 'Agrega la primera: quedará como sede principal.' : 'Un administrador puede registrarlas.'}
          </Empty>
        }
      />
      {editing && (
        <LocationDialog
          location={editing === 'new' ? null : editing}
          onClose={() => setEditing(null)}
          onSaved={() => {
            setEditing(null)
            reload()
          }}
        />
      )}
    </>
  )
}

function LocationDialog({ location, onClose, onSaved }) {
  const [form, setForm] = useState({
    name: location?.name ?? '',
    address: location?.address ?? '',
    city: location?.city ?? '',
    phone: location?.phone ?? '',
  })
  const [isMain, setIsMain] = useState(location?.is_main ?? false)
  const [errors, setErrors] = useState({})
  const [serverError, setServerError] = useState('')
  const [saving, setSaving] = useState(false)
  const field = binder(form, setForm, errors)

  async function onSave() {
    const v = toPayload(form)
    const next = {}
    if (!v.name) next.name = 'Escribe el nombre de la sede.'
    if (v.phone && !PHONE_RE.test(v.phone)) next.phone = 'Teléfono no válido.'
    setErrors(next)
    if (Object.keys(next).length) return
    setSaving(true)
    setServerError('')
    try {
      const body = { ...v, is_main: isMain }
      if (location) await businessApi.updateLocation(location.id, body)
      else await businessApi.createLocation(body)
      onSaved()
    } catch (err) {
      setServerError(err.message)
    } finally {
      setSaving(false)
    }
  }

  return (
    <FormDialog
      title={location ? 'Editar sede' : 'Nueva sede'}
      icon={<PlaceIcon />}
      onClose={onClose}
      onSubmit={onSave}
      submitting={saving}
      error={serverError}
    >
      <TextField label="Nombre" placeholder="Ej.: Sede centro" autoFocus {...field('name')} />
      <TextField label="Dirección" {...field('address')} />
      <TextField label="Ciudad o municipio" {...field('city')} />
      <TextField label="Teléfono" type="tel" {...field('phone')} />
      <FormControlLabel
        control={<Switch checked={isMain} onChange={(e) => setIsMain(e.target.checked)} />}
        label="Sede principal"
      />
    </FormDialog>
  )
}

// --- Equipo --------------------------------------------------------------------

function TeamTab() {
  const { user, isAdmin, refresh } = useAuth()
  const { data, loading, error, reload } = useApi(() => businessApi.members(), [])
  const invitations = useApi(() => (isAdmin ? businessApi.invitations() : []), [isAdmin])
  const [adding, setAdding] = useState(false)
  const [notice, setNotice] = useState(null)

  async function act(action, successText) {
    setNotice(null)
    try {
      await action()
      if (successText) setNotice({ severity: 'success', text: successText })
      reload()
    } catch (err) {
      setNotice({ severity: 'error', text: err.message })
    }
  }

  async function onLeave() {
    if (!window.confirm('¿Salir de este negocio? Dejarás de ver sus datos hasta que te vuelvan a agregar.')) return
    try {
      await businessApi.removeMember(user.id)
      await refresh() // la sesión queda sin este negocio y el layout pide elegir otro
    } catch (err) {
      setNotice({ severity: 'error', text: err.message })
    }
  }

  const columns = [
    {
      key: 'person',
      header: 'Persona',
      render: (m) => (
        <div className="flex flex-col">
          <span className="font-medium text-ink">
            {m.full_name || m.email}
            {m.user_id === user.id && <span className="text-ink-soft"> (tú)</span>}
          </span>
          {m.full_name && <span className="text-xs text-ink-soft">{m.email}</span>}
        </div>
      ),
    },
    { key: 'job_title', header: 'Cargo', hideOnMobile: true, render: (m) => m.job_title || '—' },
    {
      key: 'role',
      header: 'Rol',
      render: (m) =>
        isAdmin && m.role !== 'OWNER' && m.user_id !== user.id ? (
          <SelectField
            size="small"
            label="Rol"
            options={[
              ['MEMBER', 'Miembro'],
              ['ADMIN', 'Administrador'],
            ]}
            value={m.role}
            onChange={(role) => act(() => businessApi.changeRole(m.user_id, role), 'Rol actualizado.')}
            className="min-w-40"
          />
        ) : (
          <Stamp tone={m.role === 'OWNER' ? 'ok' : 'neutral'}>{ROLE_LABELS[m.role] ?? m.role}</Stamp>
        ),
    },
    { key: 'created_at', header: 'Desde', hideOnMobile: true, render: (m) => formatDate(m.created_at) },
    {
      key: 'actions',
      header: '',
      align: 'right',
      render: (m) => {
        if (m.role === 'OWNER') return null
        if (m.user_id === user.id)
          return <RowAction title="Salir del negocio" icon={<LogoutIcon fontSize="small" />} onClick={onLeave} />
        if (!isAdmin) return null
        return (
          <RowAction
            title="Quitar del negocio"
            color="error"
            icon={<DeleteOutlineIcon fontSize="small" />}
            onClick={() =>
              window.confirm(`¿Quitar a ${m.full_name || m.email} del negocio?`) &&
              act(() => businessApi.removeMember(m.user_id), 'Persona quitada del negocio.')
            }
          />
        )
      },
    },
  ]

  return (
    <>
      <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
        <p className="max-w-xl text-sm text-ink-soft">
          Quien pertenece a este negocio y qué puede hacer. Una persona puede estar en varios negocios.
        </p>
        {isAdmin && (
          <Button variant="contained" startIcon={<GroupAddIcon />} onClick={() => setAdding(true)}>
            Invitar persona
          </Button>
        )}
      </div>
      <Notice notice={notice} onClose={() => setNotice(null)} />
      <DataTable
        label="Equipo"
        rowKey="user_id"
        columns={columns}
        rows={data}
        loading={loading}
        error={error}
        onRetry={reload}
      />
      {isAdmin && invitations.data?.length > 0 && (
        <PendingInvitations
          rows={invitations.data}
          onRevoke={(i) =>
            window.confirm(`¿Anular la invitación a ${i.email}?`) &&
            act(async () => {
              await businessApi.revokeInvitation(i.id)
              invitations.reload()
            }, 'Invitación anulada.')
          }
        />
      )}
      {adding && <InviteDialog onClose={() => setAdding(false)} onInvited={invitations.reload} />}
    </>
  )
}

function PendingInvitations({ rows, onRevoke }) {
  const columns = [
    { key: 'email', header: 'Correo', render: (i) => <span className="font-medium text-ink">{i.email}</span> },
    { key: 'role', header: 'Rol', render: (i) => <Stamp tone="neutral">{ROLE_LABELS[i.role] ?? i.role}</Stamp> },
    { key: 'invited_by_name', header: 'Invitó', hideOnMobile: true, render: (i) => i.invited_by_name },
    { key: 'expires_at', header: 'Vence', hideOnMobile: true, render: (i) => formatDateTime(i.expires_at) },
    {
      key: 'actions',
      header: '',
      align: 'right',
      render: (i) => (
        <RowAction
          title="Anular invitación"
          color="error"
          icon={<DeleteOutlineIcon fontSize="small" />}
          onClick={() => onRevoke(i)}
        />
      ),
    },
  ]
  return (
    <div className="mt-8">
      <h2 className="mb-1 text-lg text-ink">Invitaciones pendientes</h2>
      <p className="mb-3 max-w-xl text-sm text-ink-soft">
        Esperan a que la persona abra el enlace del correo y escriba el código de seguridad. ¿Se perdió el código?
        Invítala otra vez: la invitación anterior se anula.
      </p>
      <DataTable label="Invitaciones pendientes" columns={columns} rows={rows} />
    </div>
  )
}

// Paso 1: correo + rol. Paso 2: el código de seguridad (solo se ve ahora) para dictarlo por otro medio.
function InviteDialog({ onClose, onInvited }) {
  const [email, setEmail] = useState('')
  const [role, setRole] = useState('MEMBER')
  const [error, setError] = useState('')
  const [serverError, setServerError] = useState('')
  const [saving, setSaving] = useState(false)
  const [sent, setSent] = useState(null)

  async function onSave() {
    if (!EMAIL_RE.test(email.trim())) {
      setError('Escribe un correo válido.')
      return
    }
    setError('')
    setSaving(true)
    setServerError('')
    try {
      setSent(await businessApi.invite({ email: email.trim(), role }))
      onInvited()
    } catch (err) {
      setServerError(err.message)
    } finally {
      setSaving(false)
    }
  }

  if (sent) {
    return (
      <FormDialog title="Invitación enviada" icon={<MarkEmailReadIcon />} onClose={onClose}>
        <p className="text-sm text-ink-soft">
          Enviamos un enlace a <strong className="text-ink">{sent.email}</strong>. Para aceptar, esa persona debe
          escribir este código de seguridad:
        </p>
        <p
          className="rounded-lg border border-line py-3 text-center font-mono text-3xl font-bold tracking-[0.3em] text-brand-ink"
          aria-label={`Código de seguridad ${sent.code.split('').join(' ')}`}
        >
          {sent.code}
        </p>
        <Alert severity="warning">
          Díselo tú por llamada, WhatsApp o en persona: no va en el correo. Así confirmas que entra quien quieres. Solo
          lo verás ahora; vence el {formatDateTime(sent.expires_at)}.
        </Alert>
      </FormDialog>
    )
  }

  return (
    <FormDialog
      title="Invitar persona"
      icon={<GroupAddIcon />}
      onClose={onClose}
      onSubmit={onSave}
      submitLabel="Enviar invitación"
      submittingLabel="Enviando…"
      submitting={saving}
      error={serverError}
    >
      <p className="text-sm text-ink-soft">
        La persona debe tener ya una cuenta en CantinAPP. Le llegará un correo con un enlace y tú verás un código de
        seguridad para dárselo.
      </p>
      <TextField
        label="Correo de su cuenta"
        type="email"
        value={email}
        onChange={(e) => setEmail(e.target.value)}
        error={Boolean(error)}
        helperText={error}
        fullWidth
        autoFocus
      />
      <SelectField label="Rol" options={ROLE_OPTIONS} value={role} onChange={setRole} fullWidth />
    </FormDialog>
  )
}
