import AddIcon from '@mui/icons-material/Add'
import PointOfSaleIcon from '@mui/icons-material/PointOfSale'
import UploadFileIcon from '@mui/icons-material/UploadFile'
import Alert from '@mui/material/Alert'
import Button from '@mui/material/Button'
import FormControlLabel from '@mui/material/FormControlLabel'
import Switch from '@mui/material/Switch'
import TextField from '@mui/material/TextField'
import { useState } from 'react'
import { Link as RouterLink } from 'react-router-dom'
import { salesApi } from '../api/helper'
import CsvImportDialog from '../components/ui/CsvImportDialog'
import DataTable from '../components/ui/DataTable'
import FormDialog from '../components/ui/FormDialog'
import DemoData from '../components/ui/DemoData'
import LocationFilter from '../components/ui/LocationFilter'
import { useLocationScope } from '../hooks/useLocationScope'
import PageHeader from '../components/ui/PageHeader'
import ProductPickerField from '../components/ui/ProductPicker'
import { Stamp } from '../components/ui/Stamp'
import { Empty, Notice } from '../components/ui/States'
import { useApi } from '../hooks/useApi'
import { usePagination } from '../hooks/usePagination'
import { useProductOptions } from '../hooks/useProductOptions'
import { formatCOP, formatDate, todayISO } from '../utils/format'

const dateLabel = { inputLabel: { shrink: true } }

const SOURCE_LABELS = { MANUAL: 'Manual', CSV: 'CSV', DEMO: 'Ejemplo' }

const SALE_COLUMNS = [
  { key: 'sale_date', header: 'Fecha', render: (s) => formatDate(s.sale_date) },
  {
    key: 'product_name',
    header: 'Producto',
    render: (s) => (
      <div className="flex flex-col">
        <span>{s.product_name}</span>
        {/* En el teléfono la cantidad va aquí y su columna se oculta. */}
        <span className="font-mono text-xs text-ink-soft sm:hidden">{s.quantity} u.</span>
      </div>
    ),
  },
  { key: 'quantity', header: 'Cantidad', align: 'right', mono: true, hideOnMobile: true },  { key: 'unit_price', header: 'Precio unit.', align: 'right', mono: true, hideOnMobile: true, render: (s) => formatCOP(s.unit_price) },
  { key: 'total_amount', header: 'Total', align: 'right', mono: true, render: (s) => formatCOP(s.total_amount) },
  {
    key: 'source',
    header: 'Origen',
    hideOnMobile: true,
    render: (s) => (
      <Stamp tone={s.source === 'MANUAL' ? 'ok' : 'neutral'}>{SOURCE_LABELS[s.source] ?? s.source}</Stamp>
    ),
  },
]
const LOCATION_COLUMN = { key: 'location_name', header: 'Sede', hideOnMobile: true, render: (s) => s.location_name || '—' }

export default function Sales() {
  const [product, setProduct] = useState(null)
  const [location, setLocation] = useState('')
  const { locations, own } = useLocationScope()
  const [dateFrom, setDateFrom] = useState('')
  const [dateTo, setDateTo] = useState('')
  const pager = usePagination()
  const [dialog, setDialog] = useState(null)
  const [notice, setNotice] = useState(null)

  const products = useProductOptions()
  const { data, loading, error, reload } = useApi(
    () =>
      salesApi.list({
        product_id: product?.id,
        location_id: location || undefined,
        date_from: dateFrom || undefined,
        date_to: dateTo || undefined,
        ...pager.params,
      }),
    [product, location, dateFrom, dateTo, pager.page, pager.rowsPerPage],
  )

  const filter = (setter) => (value) => {
    setter(value)
    pager.reset()
  }

  return (
    <>
      <PageHeader title="Ventas" subtitle="Registra una venta o carga tu historial por CSV.">
        <Button variant="outlined" startIcon={<UploadFileIcon />} onClick={() => setDialog('csv')}>
          Cargar CSV
        </Button>
        <Button
          variant="contained"
          startIcon={<AddIcon />}
          onClick={() => setDialog('manual')}
          disabled={products.items.length === 0}
        >
          Registrar venta
        </Button>
      </PageHeader>

      {products.data && products.items.length === 0 && (
        <Alert severity="info" className="mb-4">
          Registra productos primero para poder registrar ventas.
        </Alert>
      )}

      <div className="filter-row">
        <ProductPickerField size="small" allowAll value={product} onChange={filter(setProduct)} className="min-w-56" />
        <LocationFilter value={location} onChange={filter(setLocation)} />
        <TextField size="small" type="date" label="Desde" value={dateFrom} onChange={(e) => filter(setDateFrom)(e.target.value)} slotProps={dateLabel} />
        <TextField size="small" type="date" label="Hasta" value={dateTo} onChange={(e) => filter(setDateTo)(e.target.value)} slotProps={dateLabel} />
      </div>

      <Notice notice={notice} onClose={() => setNotice(null)} />

      <DataTable
        label="Ventas"
        columns={locations.length && !own ? [...SALE_COLUMNS, LOCATION_COLUMN] : SALE_COLUMNS}
        rows={data?.items}
        loading={loading}
        error={error}
        onRetry={reload}
        pagination={{ ...pager, total: data?.total }}
        empty={
          <Empty title="Sin ventas en este rango">
            Registra una venta o carga tu historial por CSV para ver datos aquí.
          </Empty>
        }
      />

      {dialog === 'manual' && (
        <ManualSaleDialog
          onClose={() => setDialog(null)}
          onSaved={(text) => {
            setDialog(null)
            setNotice({ severity: 'success', text })
            reload()
          }}
        />
      )}
      {dialog === 'csv' && (
        <SalesCsvDialog
          onClose={() => setDialog(null)}
          onDone={() => {
            setNotice({ severity: 'success', text: 'Carga de CSV procesada.' })
            reload()
          }}
        />
      )}
    </>
  )
}

function ManualSaleDialog({ onClose, onSaved }) {
  const { main } = useLocationScope()
  const [product, setProduct] = useState(null)
  const [location, setLocation] = useState(null) // null = la sede principal
  const [form, setForm] = useState({ sale_date: todayISO(), quantity: '1', unit_price: '' })
  const [errors, setErrors] = useState({})
  const [serverError, setServerError] = useState('')
  const [saving, setSaving] = useState(false)

  const field = (name) => ({
    value: form[name],
    onChange: (event) => setForm((f) => ({ ...f, [name]: event.target.value })),
    error: Boolean(errors[name]),
    helperText: errors[name],
    fullWidth: true,
  })

  async function onSave() {
    const next = {}
    if (!product) next.product_id = 'Elige un producto.'
    if (!form.sale_date) next.sale_date = 'Elige la fecha.'
    if (!form.quantity || Number(form.quantity) <= 0) next.quantity = 'Cantidad mayor que 0.'
    if (form.unit_price !== '' && Number(form.unit_price) < 0) next.unit_price = 'Precio 0 o más.'
    setErrors(next)
    if (Object.keys(next).length) return

    setSaving(true)
    setServerError('')
    try {
      await salesApi.create({
        product_id: product.id,
        location_id: (location ?? main) || undefined,
        sale_date: form.sale_date,
        quantity: Number(form.quantity),
        unit_price: form.unit_price === '' ? undefined : Number(form.unit_price),
      })
      onSaved('Venta registrada. El inventario se actualizó.')
    } catch (err) {
      setServerError(
        err.status === 422
          ? `No se pudo registrar: ${err.message} Revisa el stock disponible en Inventario.`
          : err.message,
      )
    } finally {
      setSaving(false)
    }
  }

  return (
    <FormDialog
      title="Registrar venta"
      icon={<PointOfSaleIcon />}
      onClose={onClose}
      onSubmit={onSave}
      submitLabel="Registrar"
      submitting={saving}
      error={serverError}
    >
      <ProductPickerField
        value={product}
        onChange={setProduct}
        error={Boolean(errors.product_id)}
        helperText={errors.product_id || (product && `Stock disponible: ${product.stock_quantity}`)}
        fullWidth
        autoFocus
      />
      <LocationFilter size="medium" value={location ?? main} onChange={setLocation} allLabel="Sin sede" fullWidth />
      <TextField type="date" label="Fecha" {...field('sale_date')} slotProps={dateLabel} />
      <TextField type="number" label="Cantidad" {...field('quantity')} />
      <TextField
        type="number"
        label="Precio unitario (opcional)"
        {...field('unit_price')}
        helperText={errors.unit_price || 'Si lo dejas vacío, se usa el precio del producto.'}
      />
    </FormDialog>
  )
}

function SalesCsvDialog({ onClose, onDone }) {
  const [affectsInventory, setAffectsInventory] = useState(false)
  const { main } = useLocationScope()
  const [location, setLocation] = useState(null) // null = la sede principal
  return (
    <CsvImportDialog
      title="Cargar historial por CSV"
      upload={(file, { confirmReimport }) =>
        salesApi.importCsv(file, affectsInventory, confirmReimport, location ?? main)
      }
      templateUrl={salesApi.templateUrl}
      onClose={onClose}
      onDone={onDone}
      next={
        <RouterLink to="/reabastecimiento" className="sketch-link self-start text-sm">
          Continuar a Reabastecimiento
        </RouterLink>
      }
    >
      <DemoData noticeOnly />
      <div className="surface-inset p-3.5 text-sm text-ink-soft">
        <p className="mb-1 font-semibold text-ink">Columnas admitidas</p>
        <p>
          <span className="font-mono">product</span> (o <span className="font-mono">product_id</span>),{' '}
          <span className="font-mono">date</span>, <span className="font-mono">quantity</span>, y opcional{' '}
          <span className="font-mono">unit_price</span>. En español: <span className="font-mono">producto</span>,{' '}
          <span className="font-mono">fecha</span>, <span className="font-mono">cantidad</span>,{' '}
          <span className="font-mono">precio</span>.
        </p>
        <p className="mt-1">
          Fechas aceptadas: <span className="font-mono">03/11/2026</span> (día/mes/año),{' '}
          <span className="font-mono">03-11-2026</span> o <span className="font-mono">2026-11-03</span>. Sin precio
          se usa el del producto.
        </p>
      </div>
      <LocationFilter
        size="medium"
        label="Sede de estas ventas"
        value={location ?? main}
        onChange={setLocation}
        allLabel="Sin sede"
        fullWidth
      />
      <FormControlLabel
        control={<Switch checked={affectsInventory} onChange={(e) => setAffectsInventory(e.target.checked)} />}
        label="Descontar del inventario"
      />
      <p className="text-xs text-ink-soft">
        Por defecto está apagado: el CSV es historial y no descuenta stock. Actívalo solo si esas ventas ya
        salieron de tu inventario.
      </p>
    </CsvImportDialog>
  )
}
