import AddShoppingCartIcon from '@mui/icons-material/AddShoppingCart'
import HistoryIcon from '@mui/icons-material/History'
import TuneIcon from '@mui/icons-material/Tune'
import TextField from '@mui/material/TextField'
import { useState } from 'react'
import { inventoryApi } from '../api/helper'
import DataTable, { RowAction } from '../components/ui/DataTable'
import FormDialog from '../components/ui/FormDialog'
import PageHeader from '../components/ui/PageHeader'
import SearchField from '../components/ui/SearchField'
import SelectField from '../components/ui/SelectField'
import { Stamp, StatusStamp } from '../components/ui/Stamp'
import { Empty, Notice } from '../components/ui/States'
import { useApi } from '../hooks/useApi'
import { useDebounced } from '../hooks/useDebounced'
import { usePagination } from '../hooks/usePagination'
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
const MOVEMENT_TYPES = {
  SALE: { label: 'Venta', tone: 'warn' },
  PURCHASE: { label: 'Compra', tone: 'ok' },
  ADJUSTMENT: { label: 'Ajuste', tone: 'neutral' },
}

export default function Inventory() {
  const [search, setSearch] = useState('')
  const debouncedSearch = useDebounced(search)
  const [status, setStatus] = useState('')
  const [sort, setSort] = useState('name')
  const pager = usePagination()
  const [movement, setMovement] = useState(null)
  const [history, setHistory] = useState(null)
  const [notice, setNotice] = useState(null)

  const { data, loading, error, reload } = useApi(
    () =>
      inventoryApi.list({
        search: debouncedSearch || undefined,
        status: status || undefined,
        sort,
        ...pager.params,
      }),
    [debouncedSearch, status, sort, pager.page, pager.rowsPerPage],
  )

  // Cambiar un filtro siempre vuelve a la página 1.
  const filter = (setter) => (value) => {
    setter(value)
    pager.reset()
  }

  const columns = [
    {
      key: 'name',
      header: 'Producto',
      render: (item) => (
        <div className="flex flex-col">
          <span className="font-medium text-ink">{item.name}</span>
          <span className="text-xs text-ink-soft">{item.category || 'Sin categoría'}</span>
        </div>
      ),
    },
    { key: 'status', header: 'Estado', render: (item) => <StatusStamp status={item.status} /> },
    { key: 'stock_quantity', header: 'Stock', align: 'right', mono: true },
    { key: 'min_stock', header: 'Mínimo', align: 'right', mono: true },
    { key: 'price', header: 'Precio', align: 'right', mono: true, hideOnMobile: true, render: (i) => formatCOP(i.price) },
    {
      key: 'actions',
      header: 'Acciones',
      align: 'right',
      className: 'whitespace-nowrap',
      render: (item) => (
        <>
          <RowAction
            title="Registrar compra"
            icon={<AddShoppingCartIcon fontSize="small" />}
            onClick={() => setMovement({ item, mode: 'purchase' })}
          />
          <RowAction
            title="Ajustar stock"
            icon={<TuneIcon fontSize="small" />}
            onClick={() => setMovement({ item, mode: 'adjust' })}
          />
          <RowAction title="Historial" icon={<HistoryIcon fontSize="small" />} onClick={() => setHistory(item)} />
        </>
      ),
    },
  ]

  return (
    <>
      <PageHeader
        title="Inventario"
        subtitle="El stock es un acumulado de movimientos: aquí no se edita directo."
      />

      <div className="filter-row">
        <SearchField value={search} onChange={filter(setSearch)} />
        <SelectField
          size="small"
          label="Estado"
          options={STATUS_OPTIONS}
          value={status}
          onChange={filter(setStatus)}
          className="min-w-44"
        />
        <SelectField
          size="small"
          label="Orden"
          options={SORTS}
          value={sort}
          onChange={filter(setSort)}
          className="min-w-40"
        />
      </div>

      <Notice notice={notice} onClose={() => setNotice(null)} />

      <DataTable
        label="Inventario"
        rowKey="product_id"
        columns={columns}
        rows={data?.items}
        loading={loading}
        error={error}
        onRetry={reload}
        pagination={{ ...pager, total: data?.total }}
        empty={
          <Empty title="Sin productos para mostrar">
            Ajusta los filtros o registra productos en la sección Productos.
          </Empty>
        }
      />

      {movement && (
        <MovementDialog
          item={movement.item}
          mode={movement.mode}
          onClose={() => setMovement(null)}
          onSaved={(text) => {
            setMovement(null)
            setNotice({ severity: 'success', text })
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
  const [quantity, setQuantity] = useState('')
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
    <FormDialog
      title={`${isPurchase ? 'Registrar compra' : 'Ajustar stock'} · ${item.name}`}
      icon={isPurchase ? <AddShoppingCartIcon /> : <TuneIcon />}
      onClose={onClose}
      onSubmit={onSave}
      submitLabel="Registrar"
      submitting={saving}
      error={serverError}
    >
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
          error || (isPurchase ? 'Cantidad mayor que 0.' : 'Ej.: 5 suma 5; -3 resta 3. No puede ser 0.')
        }
        fullWidth
        autoFocus
      />
      <TextField label="Nota (opcional)" value={notes} onChange={(e) => setNotes(e.target.value)} fullWidth />
    </FormDialog>
  )
}

const MOVEMENT_COLUMNS = [
  { key: 'created_at', header: 'Fecha', render: (m) => formatDateTime(m.created_at) },
  {
    key: 'movement_type',
    header: 'Tipo',
    render: (m) => {
      const t = MOVEMENT_TYPES[m.movement_type] ?? { label: m.movement_type, tone: 'neutral' }
      return <Stamp tone={t.tone}>{t.label}</Stamp>
    },
  },
  {
    key: 'quantity_change',
    header: 'Cambio',
    align: 'right',
    mono: true,
    render: (m) => (m.quantity_change > 0 ? `+${m.quantity_change}` : m.quantity_change),
  },
  { key: 'stock_after', header: 'Quedó en', align: 'right', mono: true },
  { key: 'notes', header: 'Nota', render: (m) => m.notes || '—' },
]

function MovementsDialog({ item, onClose }) {
  const { data, loading, error } = useApi(
    () => inventoryApi.movements(item.product_id, { limit: 50 }),
    [item.product_id],
  )

  return (
    <FormDialog title={`Movimientos de ${item.name}`} icon={<HistoryIcon />} maxWidth="sm" onClose={onClose}>
      <DataTable
        bare
        label="Movimientos"
        columns={MOVEMENT_COLUMNS}
        rows={data?.items}
        loading={loading}
        error={error}
        empty={<p className="py-6 text-center text-sm text-ink-soft">Todavía no hay movimientos.</p>}
      />
    </FormDialog>
  )
}
