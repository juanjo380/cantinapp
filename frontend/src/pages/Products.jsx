import AddIcon from '@mui/icons-material/Add'
import BlockIcon from '@mui/icons-material/Block'
import EditOutlinedIcon from '@mui/icons-material/EditOutlined'
import Inventory2OutlinedIcon from '@mui/icons-material/Inventory2Outlined'
import Button from '@mui/material/Button'
import FormControlLabel from '@mui/material/FormControlLabel'
import Switch from '@mui/material/Switch'
import TextField from '@mui/material/TextField'
import { useState } from 'react'
import { productsApi } from '../api/helper'
import DataTable, { RowAction } from '../components/ui/DataTable'
import FormDialog from '../components/ui/FormDialog'
import PageHeader from '../components/ui/PageHeader'
import SearchField from '../components/ui/SearchField'
import SelectField from '../components/ui/SelectField'
import { Stamp } from '../components/ui/Stamp'
import { Empty, Notice } from '../components/ui/States'
import { useApi } from '../hooks/useApi'
import { useDebounced } from '../hooks/useDebounced'
import { usePagination } from '../hooks/usePagination'
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
  const pager = usePagination()
  const [editing, setEditing] = useState(null)
  const [notice, setNotice] = useState(null)

  const { data, loading, error, reload } = useApi(
    () =>
      productsApi.list({
        search: debouncedSearch || undefined,
        sort,
        active_only: activeOnly,
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

  const columns = [
    {
      key: 'name',
      header: 'Producto',
      render: (p) => (
        <div className="flex flex-col">
          <span className="font-medium text-ink">{p.name}</span>
          <span className="text-xs text-ink-soft">{p.supplier || 'Sin proveedor'}</span>
        </div>
      ),
    },
    { key: 'category', header: 'Categoría', hideOnMobile: true, render: (p) => p.category || '—' },
    { key: 'price', header: 'Precio', align: 'right', mono: true, render: (p) => formatCOP(p.price) },
    { key: 'stock_quantity', header: 'Stock', align: 'right', mono: true },
    { key: 'min_stock', header: 'Mínimo', align: 'right', mono: true, hideOnMobile: true },
    {
      key: 'is_active',
      header: 'Estado',
      align: 'right',
      render: (p) => (p.is_active ? <Stamp tone="ok">Activo</Stamp> : <Stamp tone="neutral">Inactivo</Stamp>),
    },
    {
      key: 'actions',
      header: 'Acciones',
      align: 'right',
      className: 'whitespace-nowrap',
      render: (p) => (
        <>
          <RowAction title="Editar" icon={<EditOutlinedIcon fontSize="small" />} onClick={() => setEditing(p)} />
          {p.is_active && (
            <RowAction
              title="Desactivar"
              color="error"
              icon={<BlockIcon fontSize="small" />}
              onClick={() => onDeactivate(p)}
            />
          )}
        </>
      ),
    },
  ]

  return (
    <>
      <PageHeader title="Productos" subtitle="Tu catálogo. Edita los datos; el stock se mueve en Inventario.">
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
