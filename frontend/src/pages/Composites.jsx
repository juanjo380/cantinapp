import AddIcon from '@mui/icons-material/Add'
import DeleteOutlineIcon from '@mui/icons-material/DeleteOutlined'
import EditOutlinedIcon from '@mui/icons-material/EditOutlined'
import LunchDiningOutlinedIcon from '@mui/icons-material/LunchDiningOutlined'
import Button from '@mui/material/Button'
import IconButton from '@mui/material/IconButton'
import TextField from '@mui/material/TextField'
import { useState } from 'react'
import { Link as RouterLink } from 'react-router-dom'
import { productsApi } from '../api/helper'
import { useAuth } from '../auth/context'
import DataTable, { RowActions } from '../components/ui/DataTable'
import FormDialog from '../components/ui/FormDialog'
import PageHeader from '../components/ui/PageHeader'
import ProductPickerField from '../components/ui/ProductPicker'
import { Stamp } from '../components/ui/Stamp'
import { Empty, Notice } from '../components/ui/States'
import { useApi } from '../hooks/useApi'
import { formatCOP } from '../utils/format'

export default function Composites() {
  const { compositesEnabled } = useAuth()
  if (!compositesEnabled) {
    return (
      <>
        <PageHeader title="Compuestos" />
        <Empty
          icon={<LunchDiningOutlinedIcon />}
          title="La sección Compuestos está desactivada"
          action={
            <Button component={RouterLink} to="/perfil?tab=negocio" variant="contained">
              Ir a Perfil → Negocio
            </Button>
          }
        >
          El dueño del negocio puede activarla para manejar recetas de cocina.
        </Empty>
      </>
    )
  }
  return <CompositesList />
}

function CompositesList() {
  const [editing, setEditing] = useState(null) // null | 'new' | compuesto
  const [notice, setNotice] = useState(null)
  const { data, loading, error, reload } = useApi(() => productsApi.composites(), [])

  async function onRemove(composite) {
    setNotice(null)
    try {
      await productsApi.setRecipe(composite.product_id, [])
      setNotice({ severity: 'success', text: `"${composite.name}" ya no es compuesto: descuenta su propio stock.` })
      reload()
    } catch (err) {
      setNotice({ severity: 'error', text: err.message })
    }
  }

  const columns = [
    {
      key: 'name',
      header: 'Compuesto',
      render: (c) => (
        <div className="flex flex-col">
          <span className="font-medium text-ink">{c.name}</span>
          <span className="text-xs text-ink-soft">
            {c.components.map((k) => `${k.quantity} × ${k.name}`).join(', ')}
          </span>
        </div>
      ),
    },
    { key: 'price', header: 'Precio', align: 'right', mono: true, hideOnMobile: true, render: (c) => formatCOP(c.price) },
    {
      key: 'available',
      header: 'Se pueden armar',
      align: 'right',
      render: (c) =>
        c.available > 0 ? <span className="font-mono">{c.available}</span> : <Stamp tone="crit">Sin componentes</Stamp>,
    },
    {
      key: 'actions',
      header: <span className="sr-only sm:not-sr-only">Acciones</span>,
      align: 'right',
      render: (c) => (
        <RowActions
          actions={[
            { title: 'Editar receta', icon: <EditOutlinedIcon fontSize="small" />, onClick: () => setEditing(c) },
            { title: 'Quitar receta', color: 'error', icon: <DeleteOutlineIcon fontSize="small" />, onClick: () => onRemove(c) },
          ]}
        />
      ),
    },
  ]

  return (
    <>
      <PageHeader
        title="Compuestos"
        subtitle="Recetas de cocina: al vender un compuesto se descuentan sus componentes del inventario."
      >
        <Button variant="contained" startIcon={<AddIcon />} onClick={() => setEditing('new')}>
          Nuevo compuesto
        </Button>
      </PageHeader>

      <Notice notice={notice} onClose={() => setNotice(null)} />

      <DataTable
        label="Compuestos"
        columns={columns}
        rows={data}
        rowKey="product_id"
        loading={loading}
        error={error}
        onRetry={reload}
        empty={
          <Empty icon={<LunchDiningOutlinedIcon />} title="Todavía no tienes compuestos">
            Crea el producto (p. ej. «Hamburguesa») y sus ingredientes en Productos; luego arma aquí su receta.
          </Empty>
        }
      />

      {editing && (
        <RecipeDialog
          composite={editing === 'new' ? null : editing}
          onClose={() => setEditing(null)}
          onSaved={(name) => {
            setEditing(null)
            setNotice({ severity: 'success', text: `Receta de "${name}" guardada.` })
            reload()
          }}
        />
      )}
    </>
  )
}

const emptyRow = () => ({ product: null, quantity: '1' })

function RecipeDialog({ composite, onClose, onSaved }) {
  const [product, setProduct] = useState(composite && { id: composite.product_id, name: composite.name })
  const [rows, setRows] = useState(() =>
    composite
      ? composite.components.map((k) => ({ product: { id: k.component_id, name: k.name }, quantity: String(k.quantity) }))
      : [emptyRow()],
  )
  const [error, setError] = useState(null)
  const [saving, setSaving] = useState(false)
  const setRow = (index, patch) => setRows((rs) => rs.map((r, i) => (i === index ? { ...r, ...patch } : r)))

  async function onSave() {
    const ids = rows.map((r) => r.product?.id)
    const problem = !product
      ? 'Elige el producto compuesto.'
      : rows.some((r) => !r.product)
        ? 'Elige el producto de cada componente.'
        : rows.some((r) => !(Number.isInteger(Number(r.quantity)) && Number(r.quantity) >= 1))
          ? 'Cada cantidad debe ser un número entero mayor que 0.'
          : new Set(ids).size !== ids.length
            ? 'Hay componentes repetidos.'
            : ids.includes(product.id)
              ? 'Un producto no puede ser componente de sí mismo.'
              : null
    setError(problem)
    if (problem) return
    setSaving(true)
    try {
      await productsApi.setRecipe(
        product.id,
        rows.map((r) => ({ component_id: r.product.id, quantity: Number(r.quantity) })),
      )
      onSaved(product.name)
    } catch (err) {
      setError(err.message)
      setSaving(false)
    }
  }

  return (
    <FormDialog
      title={composite ? `Receta de ${composite.name}` : 'Nuevo compuesto'}
      icon={<LunchDiningOutlinedIcon />}
      onClose={onClose}
      onSubmit={onSave}
      submitting={saving}
      error={error}
      maxWidth="sm"
    >
      {!composite && (
        <ProductPickerField
          label="Producto que se vende (p. ej. Hamburguesa)"
          value={product}
          onChange={setProduct}
          fullWidth
        />
      )}
      <p className="text-sm text-ink-soft">Componentes por cada unidad vendida:</p>
      {rows.map((row, index) => (
        <div key={index} className="flex items-center gap-2">
          <ProductPickerField
            label={`Componente ${index + 1}`}
            value={row.product}
            onChange={(next) => setRow(index, { product: next })}
            className="flex-1"
          />
          <TextField
            label="Cantidad"
            type="number"
            value={row.quantity}
            onChange={(e) => setRow(index, { quantity: e.target.value })}
            slotProps={{ htmlInput: { min: 1, step: 1 } }}
            className="w-28"
          />
          <IconButton
            aria-label={`Quitar componente ${index + 1}`}
            onClick={() => setRows((rs) => rs.filter((_, i) => i !== index))}
            disabled={rows.length === 1}
          >
            <DeleteOutlineIcon fontSize="small" />
          </IconButton>
        </div>
      ))}
      <Button startIcon={<AddIcon />} onClick={() => setRows((rs) => [...rs, emptyRow()])} className="self-start">
        Agregar componente
      </Button>
    </FormDialog>
  )
}
