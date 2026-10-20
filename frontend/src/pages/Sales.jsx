import Alert from '@mui/material/Alert'
import Button from '@mui/material/Button'
import Dialog from '@mui/material/Dialog'
import DialogActions from '@mui/material/DialogActions'
import DialogContent from '@mui/material/DialogContent'
import DialogTitle from '@mui/material/DialogTitle'
import FormControlLabel from '@mui/material/FormControlLabel'
import MenuItem from '@mui/material/MenuItem'
import Switch from '@mui/material/Switch'
import Table from '@mui/material/Table'
import TableBody from '@mui/material/TableBody'
import TableCell from '@mui/material/TableCell'
import TableContainer from '@mui/material/TableContainer'
import TableHead from '@mui/material/TableHead'
import TablePagination from '@mui/material/TablePagination'
import TableRow from '@mui/material/TableRow'
import TextField from '@mui/material/TextField'
import { useState } from 'react'
import { Link as RouterLink } from 'react-router-dom'
import { productsApi, salesApi } from '../api/helper'
import PageHeader from '../components/ui/PageHeader'
import { Empty, ErrorView, Loading } from '../components/ui/States'
import { Stamp } from '../components/ui/Stamp'
import { useApi } from '../hooks/useApi'
import { formatCOP, formatDate, todayISO } from '../utils/format'

export default function Sales() {
  const [productId, setProductId] = useState('')
  const [dateFrom, setDateFrom] = useState('')
  const [dateTo, setDateTo] = useState('')
  const [page, setPage] = useState(0)
  const [rowsPerPage, setRowsPerPage] = useState(20)
  const [dialog, setDialog] = useState(null)
  const [notice, setNotice] = useState(null)

  const products = useApi(() => productsApi.list({ active_only: true, limit: 200, sort: 'name' }), [])
  const { data, loading, error, reload } = useApi(
    () =>
      salesApi.list({
        product_id: productId || undefined,
        date_from: dateFrom || undefined,
        date_to: dateTo || undefined,
        limit: rowsPerPage,
        offset: page * rowsPerPage,
      }),
    [productId, dateFrom, dateTo, page, rowsPerPage],
  )

  const items = data?.items ?? []
  const productOptions = products.data?.items ?? []

  return (
    <>
      <PageHeader title="Ventas" subtitle="Registra una venta o carga tu historial por CSV.">
        <Button variant="outlined" onClick={() => setDialog('csv')}>
          Cargar CSV
        </Button>
        <Button variant="contained" onClick={() => setDialog('manual')} disabled={productOptions.length === 0}>
          Registrar venta
        </Button>
      </PageHeader>

      {products.data && productOptions.length === 0 && (
        <Alert severity="info" className="mb-4">
          Registra productos primero para poder registrar ventas.
        </Alert>
      )}

      <div className="filter-row">
        <TextField size="small" select label="Producto" value={productId} onChange={(e) => { setProductId(e.target.value); setPage(0) }} className="min-w-56">
          <MenuItem value="">Todos</MenuItem>
          {productOptions.map((p) => (
            <MenuItem key={p.id} value={p.id}>
              {p.name}
            </MenuItem>
          ))}
        </TextField>
        <TextField size="small" type="date" label="Desde" value={dateFrom} onChange={(e) => { setDateFrom(e.target.value); setPage(0) }} InputLabelProps={{ shrink: true }} />
        <TextField size="small" type="date" label="Hasta" value={dateTo} onChange={(e) => { setDateTo(e.target.value); setPage(0) }} InputLabelProps={{ shrink: true }} />
      </div>

      {notice && (
        <Alert severity={notice.severity} className="mb-4" onClose={() => setNotice(null)}>
          {notice.text}
        </Alert>
      )}

      {loading && <Loading label="Cargando ventas…" />}
      {error && !loading && <ErrorView error={error} onRetry={reload} />}

      {!loading && !error && items.length === 0 && (
        <Empty title="Sin ventas en este rango">
          Registra una venta o carga tu historial por CSV para ver datos aquí.
        </Empty>
      )}

      {!loading && !error && items.length > 0 && (
        <div className="surface overflow-hidden">
          <TableContainer>
            <Table size="small" aria-label="Ventas">
              <TableHead>
                <TableRow>
                  <TableCell>Fecha</TableCell>
                  <TableCell>Producto</TableCell>
                  <TableCell align="right">Cantidad</TableCell>
                  <TableCell align="right">Precio unit.</TableCell>
                  <TableCell align="right">Total</TableCell>
                  <TableCell>Origen</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {items.map((sale) => (
                  <TableRow key={sale.id} hover>
                    <TableCell>{formatDate(sale.sale_date)}</TableCell>
                    <TableCell>{sale.product_name}</TableCell>
                    <TableCell align="right" className="font-mono">
                      {sale.quantity}
                    </TableCell>
                    <TableCell align="right" className="font-mono">
                      {formatCOP(sale.unit_price)}
                    </TableCell>
                    <TableCell align="right" className="font-mono">
                      {formatCOP(sale.total_amount)}
                    </TableCell>
                    <TableCell>
                      <Stamp tone={sale.source === 'CSV' ? 'neutral' : 'ok'}>
                        {sale.source === 'CSV' ? 'CSV' : 'Manual'}
                      </Stamp>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
          <TablePagination
            component="div"
            count={data.total ?? items.length}
            page={page}
            onPageChange={(_, next) => setPage(next)}
            rowsPerPage={rowsPerPage}
            onRowsPerPageChange={(e) => {
              setRowsPerPage(parseInt(e.target.value, 10))
              setPage(0)
            }}
            rowsPerPageOptions={[10, 20, 50]}
            labelRowsPerPage="Filas"
            labelDisplayedRows={({ from, to, count }) => `${from}–${to} de ${count}`}
          />
        </div>
      )}

      {dialog === 'manual' && (
        <ManualSaleDialog
          products={productOptions}
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

  const set = (field) => (event) => setForm((f) => ({ ...f, [field]: event.target.value }))

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
    <Dialog open onClose={onClose} fullWidth maxWidth="xs">
      <DialogTitle>Registrar venta</DialogTitle>
      <DialogContent className="flex flex-col gap-4 pt-2">
        {serverError && <Alert severity="error">{serverError}</Alert>}
        <TextField
          select
          label="Producto"
          value={form.product_id}
          onChange={set('product_id')}
          error={Boolean(errors.product_id)}
          helperText={errors.product_id}
          fullWidth
          autoFocus
        >
          {products.map((p) => (
            <MenuItem key={p.id} value={p.id}>
              {p.name} · stock {p.stock_quantity}
            </MenuItem>
          ))}
        </TextField>
        <TextField
          type="date"
          label="Fecha"
          value={form.sale_date}
          onChange={set('sale_date')}
          error={Boolean(errors.sale_date)}
          helperText={errors.sale_date}
          InputLabelProps={{ shrink: true }}
          fullWidth
        />
        <TextField
          type="number"
          label="Cantidad"
          value={form.quantity}
          onChange={set('quantity')}
          error={Boolean(errors.quantity)}
          helperText={errors.quantity}
          fullWidth
        />
        <TextField
          type="number"
          label="Precio unitario (opcional)"
          value={form.unit_price}
          onChange={set('unit_price')}
          error={Boolean(errors.unit_price)}
          helperText={errors.unit_price || 'Si lo dejas vacío, se usa el precio del producto.'}
          fullWidth
        />
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose}>Cancelar</Button>
        <Button variant="contained" onClick={onSave} disabled={saving}>
          {saving ? 'Guardando…' : 'Registrar'}
        </Button>
      </DialogActions>
    </Dialog>
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
    <Dialog open onClose={onClose} fullWidth maxWidth="md">
      <DialogTitle> Cargar historial por CSV</DialogTitle>
      <DialogContent className="flex flex-col gap-4 pt-2">
        {error && <Alert severity="error">{error}</Alert>}
        <div className="rounded-md border border-line bg-ground p-3.5 text-sm text-ink-soft">
          <p className="mb-1 font-semibold text-ink">Columnas admitidas</p>
          <p>
            <span className="font-mono">product</span> (o{' '}
            <span className="font-mono">product_id</span>),{' '}
            <span className="font-mono">date</span> (YYYY-MM-DD o DD/MM/YYYY),{' '}
            <span className="font-mono">quantity</span>, y opcional{' '}
            <span className="font-mono">unit_price</span>.
          </p>
        </div>
        <input
          type="file"
          accept=".csv,text/csv"
          onChange={(e) => setFile(e.target.files?.[0] ?? null)}
          className="block w-full text-sm text-ink-soft file:mr-3 file:rounded-sm file:border file:border-line file:bg-panel file:px-3 file:py-2 file:text-sm file:font-semibold file:text-ink"
        />
        <FormControlLabel
          control={<Switch checked={affectsInventory} onChange={(e) => setAffectsInventory(e.target.checked)} />}
          label="Descontar del inventario"
        />
        <p className="text-xs text-ink-soft">
          Por defecto está apagado: el CSV es historial y no descuenta stock. Actívalo solo si esas
          ventas ya salieron de tu inventario.
        </p>

        {result && (
          <div className="flex flex-col gap-3">
            <Alert severity={result.error_rows > 0 ? 'warning' : 'success'}>
              {result.imported_rows} de {result.total_rows} filas importadas; {result.error_rows} con
              error.
            </Alert>
            {result.errors?.length > 0 && (
              <TableContainer className="max-h-64">
                <Table size="small" stickyHeader>
                  <TableHead>
                    <TableRow>
                      <TableCell>Fila</TableCell>
                      <TableCell>Campo</TableCell>
                      <TableCell>Mensaje</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {result.errors.map((e, i) => (
                      <TableRow key={i}>
                        <TableCell className="font-mono">{e.row}</TableCell>
                        <TableCell>{e.field}</TableCell>
                        <TableCell>{e.message}</TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>
            )}
            <RouterLink to="/reabastecimiento" className="text-sm font-semibold text-brand underline">
              Continuar a Reabastecimiento
            </RouterLink>
          </div>
        )}
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose}>{result ? 'Cerrar' : 'Cancelar'}</Button>
        <Button variant="contained" onClick={onUpload} disabled={loading}>
          {loading ? 'Subiendo…' : 'Cargar CSV'}
        </Button>
      </DialogActions>
    </Dialog>
  )
}
