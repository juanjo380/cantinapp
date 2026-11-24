import AddIcon from '@mui/icons-material/Add'
import BlockIcon from '@mui/icons-material/Block'
import CheckCircleOutlineIcon from '@mui/icons-material/CheckCircleOutlineOutlined'
import EditOutlinedIcon from '@mui/icons-material/EditOutlined'
import LocalOfferOutlinedIcon from '@mui/icons-material/LocalOfferOutlined'
import UploadFileIcon from '@mui/icons-material/UploadFile'
import Inventory2OutlinedIcon from '@mui/icons-material/Inventory2Outlined'
import Alert from '@mui/material/Alert'
import Button from '@mui/material/Button'
import FormControlLabel from '@mui/material/FormControlLabel'
import Switch from '@mui/material/Switch'
import Tooltip from '@mui/material/Tooltip'
import TextField from '@mui/material/TextField'
import { useState } from 'react'
import { DISCOUNTS_EVENT, productsApi } from '../api/helper'
import CsvImportDialog from '../components/ui/CsvImportDialog'
import DataTable, { RowActions } from '../components/ui/DataTable'
import FormDialog from '../components/ui/FormDialog'
import PageHeader from '../components/ui/PageHeader'
import SearchField from '../components/ui/SearchField'
import SelectField from '../components/ui/SelectField'
import { Stamp } from '../components/ui/Stamp'
import { Empty, Notice } from '../components/ui/States'
import { useApi } from '../hooks/useApi'
import { useDebounced } from '../hooks/useDebounced'
import { usePagination } from '../hooks/usePagination'
import { formatCOP, formatDate, formatNumber } from '../utils/format'

const SORTS = [
  ['name', 'Nombre (A-Z)'],
  ['-name', 'Nombre (Z-A)'],
  ['price', 'Precio (menor)'],
  ['-price', 'Precio (mayor)'],
  ['stock', 'Stock (menor)'],
  ['-stock', 'Stock (mayor)'],
  ['-created', 'Más recientes'],
]

export default function Products() {
  const [search, setSearch] = useState('')
  const debouncedSearch = useDebounced(search)
  const [sort, setSort] = useState('name')
  const [activeOnly, setActiveOnly] = useState(true)
  const pager = usePagination()
  const [editing, setEditing] = useState(null)
  const [importing, setImporting] = useState(false)
  const [notice, setNotice] = useState(null)
  const [discounting, setDiscounting] = useState(null) // producto al que se aplica descuento
  const [reviewing, setReviewing] = useState(false) // lista de sugerencias abierta

  // Opcional: si falla (p. ej. falta la migración 012) la página sigue funcionando sin sugerencias.
  const discounts = useApi(() => productsApi.discounts().catch(() => null), [])
  const suggestions = discounts.data?.items ?? []
  const suggestionFor = (id) => suggestions.find((s) => s.product_id === id)
  const activeFor = (id) => discounts.data?.active?.find((d) => d.product_id === id)

  const { data, loading, error, reload } = useApi(
    () =>
      productsApi.list({
        search: debouncedSearch || undefined,
        sort,
        active_only: activeOnly,
        composite: false, // los compuestos se manejan en su propia sección
        ...pager.params,
      }),
    [debouncedSearch, sort, activeOnly, pager.page, pager.rowsPerPage],
  )

  async function onDeactivate(product) {
    setNotice(null)
    try {
      await productsApi.remove(product.id)
      setNotice({
        severity: 'success',
        text: `"${product.name}" quedó inactivo. El historial de ventas se conserva.`,
      })
      reload()
    } catch (err) {
      setNotice({ severity: 'error', text: err.message })
    }
  }

  async function onActivate(product) {
    setNotice(null)
    try {
      await productsApi.update(product.id, { is_active: true })
      setNotice({ severity: 'success', text: `"${product.name}" volvió a estar activo.` })
      reload()
    } catch (err) {
      setNotice({ severity: 'error', text: err.message })
    }
  }

  const columns = [
    {
      key: 'name',
      header: 'Producto',
      render: (p) => (
        <div className="flex flex-col">
          <span className="font-medium text-ink">{p.name}</span>
          <span className="text-xs text-ink-soft">{p.supplier || 'Sin proveedor'}</span>
          {suggestionFor(p.id) && (
            <span className="mt-1">
              <Stamp tone="warn" icon={<LocalOfferOutlinedIcon style={{ fontSize: '1rem' }} />}>
                Sugerido −{suggestionFor(p.id).percent}%
              </Stamp>
            </span>
          )}
        </div>
      ),
    },
    { key: 'category', header: 'Categoría', hideOnMobile: true, render: (p) => p.category || '—' },
    {
      key: 'price',
      header: 'Precio',
      align: 'right',
      mono: true,
      render: (p) => <PriceCell price={p.price} discount={activeFor(p.id)} />,
    },
    { key: 'stock_quantity', header: 'Stock', align: 'right', mono: true },
    { key: 'min_stock', header: 'Mínimo', align: 'right', mono: true, hideOnMobile: true },
    {
      key: 'is_active',
      header: 'Estado',
      align: 'right',
      hideOnMobile: true, // en el teléfono manda el filtro «Solo activos»
      render: (p) => (p.is_active ? <Stamp tone="ok">Activo</Stamp> : <Stamp tone="neutral">Inactivo</Stamp>),
    },
    {
      key: 'actions',
      header: <span className="sr-only sm:not-sr-only">Acciones</span>, // el «⋮» del teléfono no necesita título
      align: 'right',
      render: (p) => (
        <RowActions
          actions={[
            { title: 'Editar', icon: <EditOutlinedIcon fontSize="small" />, onClick: () => setEditing(p) },
            p.is_active && {
              title: 'Descuento',
              icon: <LocalOfferOutlinedIcon fontSize="small" />,
              onClick: () => setDiscounting(p),
            },
            p.is_active
              ? {
                  title: 'Desactivar',
                  color: 'error',
                  icon: <BlockIcon fontSize="small" />,
                  onClick: () => onDeactivate(p),
                }
              : { title: 'Activar', icon: <CheckCircleOutlineIcon fontSize="small" />, onClick: () => onActivate(p) },
          ]}
        />
      ),
    },
  ]

  return (
    <>
      <PageHeader title="Productos" subtitle="Tu catálogo. Edita los datos; el stock se mueve en Inventario.">
        <Button variant="outlined" startIcon={<UploadFileIcon />} onClick={() => setImporting(true)}>
          Cargar CSV
        </Button>
        <Button variant="contained" startIcon={<AddIcon />} onClick={() => setEditing('new')}>
          Nuevo producto
        </Button>
      </PageHeader>

      <div className="filter-row">
        <SearchField
          value={search}
          onChange={(value) => {
            setSearch(value)
            pager.reset()
          }}
        />
        <SelectField
          size="small"
          label="Orden"
          options={SORTS}
          value={sort}
          onChange={(value) => {
            setSort(value)
            pager.reset()
          }}
          className="min-w-44"
        />
        <FormControlLabel
          control={
            <Switch
              checked={activeOnly}
              onChange={(e) => {
                setActiveOnly(e.target.checked)
                pager.reset()
              }}
            />
          }
          label="Solo activos"
        />
      </div>

      <Notice notice={notice} onClose={() => setNotice(null)} />

      {suggestions.length > 0 && (
        <Alert
          severity="warning"
          icon={<LocalOfferOutlinedIcon />}
          className="mb-4"
          action={
            <Button color="inherit" size="small" onClick={() => setReviewing(true)}>
              Revisar
            </Button>
          }
        >
          {suggestions.length === 1 ? '1 producto vende' : `${suggestions.length} productos venden`} al menos un 70%
          menos que el promedio de tu negocio en los últimos {discounts.data.days} días. Un descuento puede ayudar a
          moverlos.
        </Alert>
      )}

      <DataTable
        label="Productos"
        columns={columns}
        rows={data?.items}
        loading={loading}
        error={error}
        onRetry={reload}
        pagination={{ ...pager, total: data?.total }}
        empty={
          <Empty
            title="Aún no tienes productos"
            action={
              <Button variant="contained" startIcon={<AddIcon />} onClick={() => setEditing('new')}>
                Crear el primero
              </Button>
            }
          >
            Registra tus productos para empezar a controlar stock y ventas.
          </Empty>
        }
      />

      {importing && (
        <CsvImportDialog
          title="Cargar productos por CSV"
          upload={(file) => productsApi.importCsv(file)}
          templateUrl={productsApi.templateUrl}
          onClose={() => setImporting(false)}
          onDone={(result) => {
            if (result.imported_rows > 0) {
              setNotice({ severity: 'success', text: `Se crearon ${result.imported_rows} productos desde el CSV.` })
              reload()
            }
          }}
        >
          <div className="surface-inset p-3.5 text-sm text-ink-soft">
            <p className="mb-1 font-semibold text-ink">Columnas admitidas</p>
            <p>
              Obligatorias: <span className="font-mono">nombre</span> y <span className="font-mono">precio</span>.
              Opcionales: <span className="font-mono">categoria</span>, <span className="font-mono">proveedor</span>,{' '}
              <span className="font-mono">stock_inicial</span>, <span className="font-mono">stock_minimo</span> y{' '}
              <span className="font-mono">dias_abastecimiento</span> (enteros; vacíos cuentan como 0). También en inglés:{' '}
              <span className="font-mono">name, price, category, supplier, quantity, min_stock, lead_time_days</span>.
            </p>
          </div>
          <p className="text-xs text-ink-soft">
            Los productos que ya existen (mismo nombre) no se modifican: se reportan como error de esa fila.
          </p>
        </CsvImportDialog>
      )}

      {reviewing && (
        <SuggestionsDialog
          data={discounts.data}
          onClose={() => setReviewing(false)}
          onPick={(s) => {
            setReviewing(false)
            setDiscounting({ id: s.product_id, name: s.name, price: s.price })
          }}
        />
      )}

      {discounting && (
        <DiscountDialog
          product={discounting}
          suggestion={suggestionFor(discounting.id)}
          active={activeFor(discounting.id)}
          days={discounts.data?.days}
          onClose={() => setDiscounting(null)}
          onDone={(text) => {
            setDiscounting(null)
            setNotice({ severity: 'success', text })
            reload()
            discounts.reload()
            window.dispatchEvent(new Event(DISCOUNTS_EVENT))
          }}
        />
      )}

      {editing && (
        <ProductDialog
          product={editing === 'new' ? null : editing}
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

function ProductDialog({ product, onClose, onSaved }) {
  const isNew = !product
  const [form, setForm] = useState(() => ({
    name: product?.name ?? '',
    category: product?.category ?? '',
    supplier: product?.supplier ?? '',
    price: product?.price != null ? String(product.price) : '',
    quantity: '0',
    min_stock: product?.min_stock != null ? String(product.min_stock) : '0',
    lead_time_days: product?.lead_time_days != null ? String(product.lead_time_days) : '0',
  }))
  const [errors, setErrors] = useState({})
  const [serverError, setServerError] = useState('')
  const [saving, setSaving] = useState(false)

  // Props comunes de cada campo: valor, cambio y error de validación.
  const field = (name) => ({
    value: form[name],
    onChange: (event) => setForm((f) => ({ ...f, [name]: event.target.value })),
    error: Boolean(errors[name]),
    helperText: errors[name],
    fullWidth: true,
  })

  async function onSave() {
    const next = {}
    if (!form.name.trim()) next.name = 'Escribe el nombre.'
    if (form.price === '' || Number(form.price) < 0) next.price = 'El precio debe ser 0 o más.'
    if (isNew && (form.quantity === '' || Number(form.quantity) < 0))
      next.quantity = 'La cantidad debe ser 0 o más.'
    if (Number(form.min_stock) < 0) next.min_stock = 'Debe ser 0 o más.'
    if (Number(form.lead_time_days) < 0) next.lead_time_days = 'Debe ser 0 o más.'
    setErrors(next)
    if (Object.keys(next).length) return

    setSaving(true)
    setServerError('')
    try {
      const payload = {
        name: form.name.trim(),
        category: form.category.trim() || undefined,
        supplier: form.supplier.trim() || undefined,
        price: Number(form.price),
        min_stock: Number(form.min_stock),
        lead_time_days: Number(form.lead_time_days),
      }
      if (isNew) await productsApi.create({ ...payload, quantity: Number(form.quantity) })
      else await productsApi.update(product.id, payload)
      onSaved()
    } catch (err) {
      setServerError(err.message)
    } finally {
      setSaving(false)
    }
  }

  return (
    <FormDialog
      title={isNew ? 'Nuevo producto' : 'Editar producto'}
      icon={<Inventory2OutlinedIcon />}
      maxWidth="sm"
      onClose={onClose}
      onSubmit={onSave}
      submitting={saving}
      error={serverError}
    >
      <TextField label="Nombre" {...field('name')} autoFocus />
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
        <TextField label="Categoría" {...field('category')} />
        <TextField label="Proveedor" {...field('supplier')} />
        <TextField label="Precio (COP)" type="number" {...field('price')} />
        {isNew && <TextField label="Stock inicial" type="number" {...field('quantity')} />}
        <TextField label="Stock mínimo" type="number" {...field('min_stock')} />
        <TextField label="Abastecimiento (días)" type="number" {...field('lead_time_days')} />
      </div>
      {!isNew && (
        <p className="text-xs text-ink-soft">
          El stock no se edita aquí: usa Inventario → Registrar compra o Ajustar stock.
        </p>
      )}
    </FormDialog>
  )
}

// Precio con descuento vigente: etiqueta «−N%», precio actual y el de lista tachado.
function PriceCell({ price, discount }) {
  if (!discount) return formatCOP(price)
  return (
    <Tooltip
      title={`Precio de lista ${formatCOP(discount.price_before)} · descuento aplicado el ${formatDate(discount.discounted_at)}`}
    >
      <span tabIndex={0} className="inline-flex flex-col items-end gap-0.5 outline-offset-2">
        <span className="inline-flex items-center gap-2">
          <DiscountTag percent={discount.percent} />
          <span className="font-bold text-ink">{formatCOP(price)}</span>
        </span>
        <span className="text-xs text-ink-soft line-through" aria-hidden="true">
          {formatCOP(discount.price_before)}
        </span>
        <span className="sr-only">
          con descuento del {discount.percent}%, precio de lista {formatCOP(discount.price_before)}
        </span>
      </span>
    </Tooltip>
  )
}

// Etiqueta con forma de marbete de precio (punta y ojal a la izquierda). Texto oscuro sobre naranja por contraste.
function DiscountTag({ percent }) {
  return (
    <span
      aria-hidden="true"
      className="relative inline-flex items-center bg-brand py-0.5 pr-1.5 pl-3.5 font-mono text-xs leading-4 font-bold text-brand-contrast [clip-path:polygon(9px_0,100%_0,100%_100%,9px_100%,0_50%)]"
    >
      <span className="absolute top-1/2 left-[7px] h-1 w-1 -translate-y-1/2 rounded-full bg-ground" />−{percent}%
    </span>
  )
}

// Mismo redondeo que el backend (discounts.py): múltiplos de 50 COP.
const discountedPrice = (price, percent) => Math.round((Number(price) * (100 - percent)) / 100 / 50) * 50

function SuggestionsDialog({ data, onClose, onPick }) {
  return (
    <FormDialog title="Descuentos sugeridos" icon={<LocalOfferOutlinedIcon />} maxWidth="sm" onClose={onClose}>
      <p className="text-sm text-ink-soft">
        Productos con stock que en los últimos {data.days} días vendieron menos del 30% del promedio por producto del
        negocio ({formatNumber(data.items[0]?.business_avg)} u). Sin ventas: −30%; muy bajas: −20%; bajas: −10%.
      </p>
      <ul className="flex flex-col gap-2">
        {data.items.map((s) => (
          <li key={s.product_id} className="surface-inset flex flex-wrap items-center gap-3 p-3">
            <div className="min-w-0 flex-1">
              <p className="truncate font-medium text-ink">{s.name}</p>
              <p className="text-xs text-ink-soft">
                {formatNumber(s.units)} u vendidas · stock {formatNumber(s.stock)}
                {s.coverage_days != null ? ` (≈${formatNumber(s.coverage_days)} días)` : ''}
                {' · '}
                {s.last_sale ? `última venta ${formatDate(s.last_sale)}` : 'nunca se ha vendido'}
              </p>
              <p className="font-mono text-sm">
                <span className="text-ink-soft line-through">{formatCOP(s.price)}</span>{' '}
                <span className="font-bold text-ink">{formatCOP(s.suggested_price)}</span>{' '}
                <span className="text-brand-ink">−{s.percent}%</span>
              </p>
            </div>
            <Button variant="outlined" size="small" onClick={() => onPick(s)}>
              Aplicar
            </Button>
          </li>
        ))}
      </ul>
    </FormDialog>
  )
}

function DiscountDialog({ product, suggestion, active, days, onClose, onDone }) {
  const [percent, setPercent] = useState(String(suggestion?.percent ?? active?.percent ?? 10))
  const [error, setError] = useState('')
  const [saving, setSaving] = useState(false)
  const value = Number(percent)
  const valid = Number.isInteger(value) && value >= 1 && value <= 90
  // El porcentaje se calcula sobre el precio de lista, igual que en el backend.
  const listPrice = active?.price_before ?? product.price
  const newPrice = valid ? discountedPrice(listPrice, value) : null

  async function run(action) {
    setSaving(true)
    setError('')
    try {
      onDone(await action())
    } catch (err) {
      setError(err.message)
    } finally {
      setSaving(false)
    }
  }

  function onSubmit() {
    if (!valid) return setError('El descuento debe ser un entero entre 1 y 90.')
    run(async () => {
      const updated = await productsApi.applyDiscount(product.id, value)
      return `"${updated.name}" ahora cuesta ${formatCOP(updated.price)} (−${value}% sobre ${formatCOP(listPrice)}).`
    })
  }

  const onRemove = () =>
    run(async () => {
      const updated = await productsApi.removeDiscount(product.id)
      return `"${updated.name}" volvió a su precio de lista: ${formatCOP(updated.price)}.`
    })

  return (
    <FormDialog
      title={`Descuento: ${product.name}`}
      icon={<LocalOfferOutlinedIcon />}
      onClose={onClose}
      onSubmit={onSubmit}
      submitLabel="Aplicar descuento"
      submittingLabel="Aplicando…"
      submitting={saving}
      error={error}
    >
      {active && (
        <div className="surface-inset flex flex-wrap items-center gap-3 p-3">
          <DiscountTag percent={active.percent} />
          <p className="min-w-0 flex-1 text-sm text-ink-soft">
            Precio de lista <span className="font-mono">{formatCOP(active.price_before)}</span>, aplicado el{' '}
            {formatDate(active.discounted_at)}.
          </p>
          <Button size="small" color="inherit" variant="outlined" onClick={onRemove} disabled={saving}>
            Quitar descuento
          </Button>
        </div>
      )}
      {suggestion && (
        <p className="text-sm text-ink-soft">
          Vendió {formatNumber(suggestion.units)} u en los últimos {days} días frente a un promedio de{' '}
          {formatNumber(suggestion.business_avg)} u por producto. Se sugiere −{suggestion.percent}%.
        </p>
      )}
      <TextField
        label="Descuento (%)"
        type="number"
        value={percent}
        onChange={(e) => setPercent(e.target.value)}
        error={!valid}
        helperText={valid ? 'Entre 1 y 90. El precio se redondea a múltiplos de 50.' : 'Debe ser un entero entre 1 y 90.'}
        slotProps={{ htmlInput: { min: 1, max: 90, step: 1 } }}
        autoFocus
        fullWidth
      />
      <p className="font-mono text-sm" aria-live="polite">
        {formatCOP(listPrice)} →{' '}
        <span className="font-bold text-ink">{newPrice != null ? formatCOP(newPrice) : '—'}</span>
      </p>
      <p className="text-xs text-ink-soft">
        Cambia el precio de venta; las ventas ya registradas conservan su precio. El precio de lista se guarda para
        mostrar la etiqueta y poder quitar el descuento. No se sugerirá otro descuento mientras este siga activo.
      </p>
    </FormDialog>
  )
}
