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
import { productsApi } from '../api/helper'
import PageHeader from '../components/ui/PageHeader'
import { Stamp } from '../components/ui/Stamp'
import { Empty, ErrorView, Loading } from '../components/ui/States'
import { useApi } from '../hooks/useApi'
import { useDebounced } from '../hooks/useDebounced'
import { formatCOP } from '../utils/format'

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
  const [page, setPage] = useState(0)
  const [rowsPerPage, setRowsPerPage] = useState(20)
  const [editing, setEditing] = useState(null)
  const [notice, setNotice] = useState(null)

  const { data, loading, error, reload } = useApi(
    () =>
      productsApi.list({
        search: debouncedSearch || undefined,
        sort,
        active_only: activeOnly,
        limit: rowsPerPage,
        offset: page * rowsPerPage,
      }),
    [debouncedSearch, sort, activeOnly, page, rowsPerPage],
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

  const items = data?.items ?? []

  return (
    <>
      <PageHeader
        title="Productos"
        subtitle="Tu catálogo. Edita los datos; el stock se mueve en Inventario."
      >
        <Button variant="contained" onClick={() => setEditing('new')}>
          Nuevo producto
        </Button>
      </PageHeader>

      <div className="filter-row">
        <TextField size="small" label="Buscar" value={search} onChange={(e) => setSearch(e.target.value)} />
        <TextField
          size="small"
          select
          label="Orden"
          value={sort}
          onChange={(e) => setSort(e.target.value)}
          className="min-w-44"
        >
          {SORTS.map(([value, label]) => (
            <MenuItem key={value} value={value}>
              {label}
            </MenuItem>
          ))}
        </TextField>
        <FormControlLabel
          control={<Switch checked={activeOnly} onChange={(e) => setActiveOnly(e.target.checked)} />}
          label="Solo activos"
        />
      </div>

      {notice && (
        <Alert severity={notice.severity} className="mb-4" onClose={() => setNotice(null)}>
          {notice.text}
        </Alert>
      )}

      {loading && <Loading label="Cargando productos…" />}
      {error && !loading && <ErrorView error={error} onRetry={reload} />}

      {!loading && !error && items.length === 0 && (
        <Empty
          title="Aún no tienes productos"
          action={
            <Button variant="contained" onClick={() => setEditing('new')}>
              Crear el primero
            </Button>
          }
        >
          Registra tus productos para empezar a controlar stock y ventas.
        </Empty>
      )}

      {!loading && !error && items.length > 0 && (
        <div className="surface overflow-hidden">
          <TableContainer>
            <Table size="small" aria-label="Productos">
              <TableHead>
                <TableRow>
                  <TableCell>Producto</TableCell>
                  <TableCell className="hidden sm:table-cell">Categoría</TableCell>
                  <TableCell align="right">Precio</TableCell>
                  <TableCell align="right">Stock</TableCell>
                  <TableCell align="right" className="hidden sm:table-cell">
                    Mínimo
                  </TableCell>
                  <TableCell align="right">Estado</TableCell>
                  <TableCell align="right">Acciones</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {items.map((p) => (
                  <TableRow key={p.id} hover>
                    <TableCell>
                      <div className="flex flex-col">
                        <span className="font-medium text-ink">{p.name}</span>
                        <span className="text-xs text-ink-soft">{p.supplier || 'Sin proveedor'}</span>
                      </div>
                    </TableCell>
                    <TableCell className="hidden sm:table-cell">{p.category || '—'}</TableCell>
                    <TableCell align="right" className="font-mono">
                      {formatCOP(p.price)}
                    </TableCell>
                    <TableCell align="right" className="font-mono">
                      {p.stock_quantity}
                    </TableCell>
                    <TableCell align="right" className="hidden font-mono sm:table-cell">
                      {p.min_stock}
                    </TableCell>
                    <TableCell align="right">
                      {p.is_active ? (
                        <Stamp tone="ok">Activo</Stamp>
                      ) : (
                        <Stamp tone="neutral">Inactivo</Stamp>
                      )}
                    </TableCell>
                    <TableCell align="right" className="whitespace-nowrap">
                      <Button size="small" onClick={() => setEditing(p)}>
                        Editar
                      </Button>
                      {p.is_active && (
                        <Button size="small" color="error" onClick={() => onDeactivate(p)}>
                          Desactivar
                        </Button>
                      )}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
          <TablePagination
            component="div"
            count={data.total}
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

  const set = (field) => (event) => setForm((f) => ({ ...f, [field]: event.target.value }))

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
    <Dialog open onClose={onClose} fullWidth maxWidth="sm">
      <DialogTitle>{isNew ? 'Nuevo producto' : 'Editar producto'}</DialogTitle>
      <DialogContent className="flex flex-col gap-4 pt-2">
        {serverError && <Alert severity="error">{serverError}</Alert>}
        <TextField
          label="Nombre"
          value={form.name}
          onChange={set('name')}
          error={Boolean(errors.name)}
          helperText={errors.name}
          fullWidth
          autoFocus
        />
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
          <TextField label="Categoría" value={form.category} onChange={set('category')} fullWidth />
          <TextField label="Proveedor" value={form.supplier} onChange={set('supplier')} fullWidth />
          <TextField
            label="Precio (COP)"
            type="number"
            value={form.price}
            onChange={set('price')}
            error={Boolean(errors.price)}
            helperText={errors.price}
            fullWidth
          />
          {isNew && (
            <TextField
              label="Stock inicial"
              type="number"
              value={form.quantity}
              onChange={set('quantity')}
              error={Boolean(errors.quantity)}
              helperText={errors.quantity}
              fullWidth
            />
          )}
          <TextField
            label="Stock mínimo"
            type="number"
            value={form.min_stock}
            onChange={set('min_stock')}
            error={Boolean(errors.min_stock)}
            helperText={errors.min_stock}
            fullWidth
          />
          <TextField
            label="Abastecimiento (días)"
            type="number"
            value={form.lead_time_days}
            onChange={set('lead_time_days')}
            error={Boolean(errors.lead_time_days)}
            helperText={errors.lead_time_days}
            fullWidth
          />
        </div>
        {!isNew && (
          <p className="text-xs text-ink-soft">
            El stock no se edita aquí: usa Inventario → Registrar compra o Ajustar stock.
          </p>
        )}
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose}>Cancelar</Button>
        <Button variant="contained" onClick={onSave} disabled={saving}>
          {saving ? 'Guardando…' : 'Guardar'}
        </Button>
      </DialogActions>
    </Dialog>
  )
}
