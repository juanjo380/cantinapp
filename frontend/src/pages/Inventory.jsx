import Alert from '@mui/material/Alert'
import Button from '@mui/material/Button'
import Dialog from '@mui/material/Dialog'
import DialogActions from '@mui/material/DialogActions'
import DialogContent from '@mui/material/DialogContent'
import DialogTitle from '@mui/material/DialogTitle'
import MenuItem from '@mui/material/MenuItem'
import Table from '@mui/material/Table'
import TableBody from '@mui/material/TableBody'
import TableCell from '@mui/material/TableCell'
import TableContainer from '@mui/material/TableContainer'
import TableHead from '@mui/material/TableHead'
import TablePagination from '@mui/material/TablePagination'
import TableRow from '@mui/material/TableRow'
import TextField from '@mui/material/TextField'
import { useState } from 'react'
import { inventoryApi } from '../api/helper'
import PageHeader from '../components/ui/PageHeader'
import { StatusStamp } from '../components/ui/Stamp'
import { Empty, ErrorView, Loading } from '../components/ui/States'
import { useApi } from '../hooks/useApi'
import { useDebounced } from '../hooks/useDebounced'
import { formatCOP, formatDateTime } from '../utils/format'

const STATUS_OPTIONS = [
  ['', 'Todos los estados'],
  ['NORMAL', 'Normal'],
  ['BAJO', 'Bajo'],
  ['AGOTADO', 'Agotado'],
]
const SORTS = [
  ['name', 'Nombre (A-Z)'],
  ['-name', 'Nombre (Z-A)'],
  ['stock', 'Stock (menor)'],
  ['-stock', 'Stock (mayor)'],
]

export default function Inventory() {
  const [search, setSearch] = useState('')
  const debouncedSearch = useDebounced(search)
  const [status, setStatus] = useState('')
  const [sort, setSort] = useState('name')
  const [page, setPage] = useState(0)
  const [rowsPerPage, setRowsPerPage] = useState(20)
  const [movement, setMovement] = useState(null)
  const [history, setHistory] = useState(null)
  const [notice, setNotice] = useState(null)

  const { data, loading, error, reload } = useApi(
    () =>
      inventoryApi.list({
        search: debouncedSearch || undefined,
        status: status || undefined,
        sort,
        limit: rowsPerPage,
        offset: page * rowsPerPage,
      }),
    [debouncedSearch, status, sort, page, rowsPerPage],
  )

  const items = data?.items ?? []

  return (
    <>
      <PageHeader
        title="Inventario"
        subtitle="El stock es un acumulado de movimientos: aquí no se edita directo."
      />

      <div className="filter-row">
        <TextField size="small" label="Buscar" value={search} onChange={(e) => setSearch(e.target.value)} />
        <TextField
          size="small"
          select
          label="Estado"
          value={status}
          onChange={(e) => {
            setStatus(e.target.value)
            setPage(0)
          }}
          className="min-w-44"
        >
          {STATUS_OPTIONS.map(([value, label]) => (
            <MenuItem key={value} value={value}>
              {label}
            </MenuItem>
          ))}
        </TextField>
        <TextField size="small" select label="Orden" value={sort} onChange={(e) => setSort(e.target.value)} className="min-w-40">
          {SORTS.map(([value, label]) => (
            <MenuItem key={value} value={value}>
              {label}
            </MenuItem>
          ))}
        </TextField>
      </div>

      {notice && (
        <Alert severity="success" className="mb-4" onClose={() => setNotice(null)}>
          {notice}
        </Alert>
      )}

      {loading && <Loading label="Cargando inventario…" />}
      {error && !loading && <ErrorView error={error} onRetry={reload} />}

      {!loading && !error && items.length === 0 && (
        <Empty title="Sin productos para mostrar">
          Ajusta los filtros o registra productos en la sección Productos.
        </Empty>
      )}

      {!loading && !error && items.length > 0 && (
        <div className="surface overflow-hidden">
          <TableContainer>
            <Table size="small" aria-label="Inventario">
              <TableHead>
                <TableRow>
                  <TableCell>Producto</TableCell>
                  <TableCell>Estado</TableCell>
                  <TableCell align="right">Stock</TableCell>
                  <TableCell align="right">Mínimo</TableCell>
                  <TableCell align="right">Precio</TableCell>
                  <TableCell align="right">Acciones</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {items.map((item) => (
                  <TableRow key={item.product_id} hover>
                    <TableCell>
                      <div className="flex flex-col">
                        <span className="font-medium text-ink">{item.name}</span>
                        <span className="text-xs text-ink-soft">{item.category || 'Sin categoría'}</span>
                      </div>
                    </TableCell>
                    <TableCell>
                      <StatusStamp status={item.status} />
                    </TableCell>
                    <TableCell align="right" className="font-mono">
                      {item.stock_quantity}
                    </TableCell>
                    <TableCell align="right" className="font-mono">
                      {item.min_stock}
                    </TableCell>
                    <TableCell align="right" className="font-mono">
                      {formatCOP(item.price)}
                    </TableCell>
                    <TableCell align="right" className="whitespace-nowrap">
                      <Button size="small" onClick={() => setMovement({ item, mode: 'purchase' })}>
                        Compra
                      </Button>
                      <Button size="small" onClick={() => setMovement({ item, mode: 'adjust' })}>
                        Ajustar
                      </Button>
                      <Button size="small" onClick={() => setHistory(item)}>
                        Historial
                      </Button>
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

      {movement && (
        <MovementDialog
          item={movement.item}
          mode={movement.mode}
          onClose={() => setMovement(null)}
          onSaved={(text) => {
            setMovement(null)
            setNotice(text)
            reload()
          }}
        />
      )}

      {history && <MovementsDialog item={history} onClose={() => setHistory(null)} />}
    </>
  )
}

function MovementDialog({ item, mode, onClose, onSaved }) {
  const isPurchase = mode === 'purchase'
  const [quantity, setQuantity] = useState(isPurchase ? '' : '')
  const [notes, setNotes] = useState('')
  const [error, setError] = useState('')
  const [serverError, setServerError] = useState('')
  const [saving, setSaving] = useState(false)

  async function onSave() {
    const value = Number(quantity)
    let message = ''
    if (quantity === '' || Number.isNaN(value)) message = 'Escribe una cantidad.'
    else if (isPurchase && value <= 0) message = 'La compra debe ser mayor que 0.'
    else if (!isPurchase && value === 0) message = 'El ajuste no puede ser 0.'
    setError(message)
    if (message) return

    setSaving(true)
    setServerError('')
    try {
      await inventoryApi.createMovement({
        product_id: item.product_id,
        movement_type: isPurchase ? 'PURCHASE' : 'ADJUSTMENT',
        quantity_change: value,
        notes: notes.trim() || undefined,
      })
      onSaved(
        isPurchase
          ? `Compra registrada: +${value} en "${item.name}".`
          : `Ajuste registrado: ${value > 0 ? '+' : ''}${value} en "${item.name}".`,
      )
    } catch (err) {
      setServerError(err.message)
    } finally {
      setSaving(false)
    }
  }

  return (
    <Dialog open onClose={onClose} fullWidth maxWidth="xs">
      <DialogTitle>
        {isPurchase ? 'Registrar compra' : 'Ajustar stock'} · {item.name}
      </DialogTitle>
      <DialogContent className="flex flex-col gap-4 pt-2">
        {serverError && <Alert severity="error">{serverError}</Alert>}
        <p className="text-sm text-ink-soft">
          Stock actual: <span className="font-mono text-ink">{item.stock_quantity}</span>
        </p>
        <TextField
          label={isPurchase ? 'Cantidad comprada' : 'Cambio (usa negativo para restar)'}
          type="number"
          value={quantity}
          onChange={(e) => setQuantity(e.target.value)}
          error={Boolean(error)}
          helperText={
            error ||
            (isPurchase
              ? 'Cantidad mayor que 0.'
              : 'Ej.: 5 suma 5; -3 resta 3. No puede ser 0.')
          }
          fullWidth
          autoFocus
        />
        <TextField
          label="Nota (opcional)"
          value={notes}
          onChange={(e) => setNotes(e.target.value)}
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

function MovementsDialog({ item, onClose }) {
  const { data, loading, error } = useApi(
    () => inventoryApi.movements(item.product_id, { limit: 50 }),
    [item.product_id],
  )
  const movements = data?.items ?? []

  return (
    <Dialog open onClose={onClose} fullWidth maxWidth="sm">
      <DialogTitle>Movimientos de {item.name}</DialogTitle>
      <DialogContent className="pt-2">
        {loading && <Loading label="Cargando movimientos…" />}
        {error && !loading && <ErrorView error={error} />}
        {!loading && !error && movements.length === 0 && (
          <p className="py-6 text-center text-sm text-ink-soft">Todavía no hay movimientos.</p>
        )}
        {!loading && !error && movements.length > 0 && (
          <Table size="small">
            <TableHead>
              <TableRow>
                <TableCell>Fecha</TableCell>
                <TableCell>Tipo</TableCell>
                <TableCell align="right">Cambio</TableCell>
                <TableCell align="right">Quedó en</TableCell>
                <TableCell>Nota</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {movements.map((m) => (
                <TableRow key={m.id}>
                  <TableCell>{formatDateTime(m.created_at)}</TableCell>
                  <TableCell>{m.movement_type === 'PURCHASE' ? 'Compra' : 'Ajuste'}</TableCell>
                  <TableCell align="right" className="font-mono">
                    {m.quantity_change > 0 ? `+${m.quantity_change}` : m.quantity_change}
                  </TableCell>
                  <TableCell align="right" className="font-mono">
                    {m.stock_after}
                  </TableCell>
                  <TableCell>{m.notes || '—'}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        )}
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose}>Cerrar</Button>
      </DialogActions>
    </Dialog>
  )
}
