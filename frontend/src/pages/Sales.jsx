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
import DataTable from '../components/ui/DataTable'
import FormDialog from '../components/ui/FormDialog'
import PageHeader from '../components/ui/PageHeader'
import SelectField from '../components/ui/SelectField'
import { Stamp } from '../components/ui/Stamp'
import { Empty, Notice } from '../components/ui/States'
import { useApi } from '../hooks/useApi'
import { usePagination } from '../hooks/usePagination'
import { useProductOptions } from '../hooks/useProductOptions'
import { formatCOP, formatDate, todayISO } from '../utils/format'

const dateLabel = { inputLabel: { shrink: true } }

const SALE_COLUMNS = [
  { key: 'sale_date', header: 'Fecha', render: (s) => formatDate(s.sale_date) },
  { key: 'product_name', header: 'Producto' },
  { key: 'quantity', header: 'Cantidad', align: 'right', mono: true },
  { key: 'unit_price', header: 'Precio unit.', align: 'right', mono: true, hideOnMobile: true, render: (s) => formatCOP(s.unit_price) },
  { key: 'total_amount', header: 'Total', align: 'right', mono: true, render: (s) => formatCOP(s.total_amount) },
  {
    key: 'source',
    header: 'Origen',
    render: (s) => <Stamp tone={s.source === 'CSV' ? 'neutral' : 'ok'}>{s.source === 'CSV' ? 'CSV' : 'Manual'}</Stamp>,
  },
]

const CSV_ERROR_COLUMNS = [
  { key: 'row', header: 'Fila', mono: true },
  { key: 'field', header: 'Campo' },
  { key: 'message', header: 'Mensaje' },
]

export default function Sales() {
  const [productId, setProductId] = useState('')
  const [dateFrom, setDateFrom] = useState('')
  const [dateTo, setDateTo] = useState('')
  const pager = usePagination()
  const [dialog, setDialog] = useState(null)
  const [notice, setNotice] = useState(null)

  const products = useProductOptions()
  const { data, loading, error, reload } = useApi(
    () =>
      salesApi.list({
        product_id: productId || undefined,
        date_from: dateFrom || undefined,
        date_to: dateTo || undefined,
        ...pager.params,
      }),
    [productId, dateFrom, dateTo, pager.page, pager.rowsPerPage],
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
        <SelectField
          size="small"
          label="Producto"
          options={[['', 'Todos'], ...products.items.map((p) => [p.id, p.name])]}
          value={productId}
          onChange={filter(setProductId)}
          className="min-w-56"
        />
        <TextField size="small" type="date" label="Desde" value={dateFrom} onChange={(e) => filter(setDateFrom)(e.target.value)} slotProps={dateLabel} />
        <TextField size="small" type="date" label="Hasta" value={dateTo} onChange={(e) => filter(setDateTo)(e.target.value)} slotProps={dateLabel} />
      </div>

      <Notice notice={notice} onClose={() => setNotice(null)} />

      <DataTable
        label="Ventas"
        columns={SALE_COLUMNS}
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
          products={products.items}
          onClose={() => setDialog(null)}
          onSaved={(text) => {
            setDialog(null)
            setNotice({ severity: 'success', text })
            reload()
          }}
        />
      )}
      {dialog === 'csv' && (
        <CsvImportDialog
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

function ManualSaleDialog({ products, onClose, onSaved }) {
  const [form, setForm] = useState({ product_id: '', sale_date: todayISO(), quantity: '1', unit_price: '' })
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
    if (!form.product_id) next.product_id = 'Elige un producto.'
    if (!form.sale_date) next.sale_date = 'Elige la fecha.'
    if (!form.quantity || Number(form.quantity) <= 0) next.quantity = 'Cantidad mayor que 0.'
    if (form.unit_price !== '' && Number(form.unit_price) < 0) next.unit_price = 'Precio 0 o más.'
    setErrors(next)
    if (Object.keys(next).length) return

    setSaving(true)
    setServerError('')
    try {
      await salesApi.create({
        product_id: form.product_id,
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
      <SelectField
        label="Producto"
        options={products.map((p) => [p.id, `${p.name} · stock ${p.stock_quantity}`])}
        {...field('product_id')}
        onChange={(value) => setForm((f) => ({ ...f, product_id: value }))}
        autoFocus
      />
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

function CsvImportDialog({ onClose, onDone }) {
  const [file, setFile] = useState(null)
  const [affectsInventory, setAffectsInventory] = useState(false)
  const [result, setResult] = useState(null)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  async function onUpload() {
    if (!file) {
      setError('Elige un archivo CSV.')
      return
    }
    setLoading(true)
    setError('')
    try {
      const outcome = await salesApi.importCsv(file, affectsInventory)
      setResult(outcome)
      onDone()
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <FormDialog
      title="Cargar historial por CSV"
      icon={<UploadFileIcon />}
      maxWidth="md"
      onClose={onClose}
      onSubmit={onUpload}
      submitLabel="Cargar CSV"
      submittingLabel="Subiendo…"
      submitting={loading}
      cancelLabel={result ? 'Cerrar' : 'Cancelar'}
      error={error}
    >
      <div className="surface-inset p-3.5 text-sm text-ink-soft">
        <p className="mb-1 font-semibold text-ink">Columnas admitidas</p>
        <p>
          <span className="font-mono">product</span> (o <span className="font-mono">product_id</span>),{' '}
          <span className="font-mono">date</span> (YYYY-MM-DD o DD/MM/YYYY),{' '}
          <span className="font-mono">quantity</span>, y opcional <span className="font-mono">unit_price</span>.
        </p>
      </div>
      <Button component="label" variant="outlined" startIcon={<UploadFileIcon />} className="self-start">
        {file ? file.name : 'Elegir archivo CSV'}
        <input type="file" hidden accept=".csv,text/csv" onChange={(e) => setFile(e.target.files?.[0] ?? null)} />
      </Button>
      <FormControlLabel
        control={<Switch checked={affectsInventory} onChange={(e) => setAffectsInventory(e.target.checked)} />}
        label="Descontar del inventario"
      />
      <p className="text-xs text-ink-soft">
        Por defecto está apagado: el CSV es historial y no descuenta stock. Actívalo solo si esas ventas ya
        salieron de tu inventario.
      </p>

      {result && (
        <div className="flex flex-col gap-3">
          <Alert severity={result.error_rows > 0 ? 'warning' : 'success'}>
            {result.imported_rows} de {result.total_rows} filas importadas; {result.error_rows} con error.
          </Alert>
          {result.errors?.length > 0 && (
            <DataTable label="Errores del CSV" columns={CSV_ERROR_COLUMNS} rows={result.errors} maxHeight={256} />
          )}
          <RouterLink to="/reabastecimiento" className="sketch-link self-start text-sm">
            Continuar a Reabastecimiento
          </RouterLink>
        </div>
      )}
    </FormDialog>
  )
}
