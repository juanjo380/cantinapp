import ClearIcon from '@mui/icons-material/Clear'
import Inventory2OutlinedIcon from '@mui/icons-material/Inventory2Outlined'
import SearchIcon from '@mui/icons-material/Search'
import Button from '@mui/material/Button'
import IconButton from '@mui/material/IconButton'
import InputAdornment from '@mui/material/InputAdornment'
import TextField from '@mui/material/TextField'
import { useState } from 'react'
import { productsApi } from '../../api/helper'
import { useApi } from '../../hooks/useApi'
import { useDebounced } from '../../hooks/useDebounced'
import { usePagination } from '../../hooks/usePagination'
import { useProductOptions } from '../../hooks/useProductOptions'
import { formatCOP } from '../../utils/format'
import DataTable from './DataTable'
import FormDialog from './FormDialog'
import SearchField from './SearchField'
import SelectField from './SelectField'
import { Empty } from './States'

const SORTS = [
  ['name', 'Nombre (A-Z)'],
  ['-stock', 'Más stock'],
  ['stock', 'Menos stock'],
  ['price', 'Precio (menor)'],
  ['-price', 'Precio (mayor)'],
]

// Campo que abre un modal para buscar y elegir un producto. `value` es el producto elegido (o null).
// Con `allowAll`, vacío significa «Todos» y se puede limpiar.
export default function ProductPickerField({ value, onChange, label = 'Producto', allowAll = false, ...props }) {
  const [open, setOpen] = useState(false)
  const openPicker = () => setOpen(true)
  return (
    <>
      <TextField
        label={label}
        value={value?.name ?? (allowAll ? 'Todos' : '')}
        onClick={openPicker}
        onKeyDown={(e) => {
          if (e.key === 'Enter' || e.key === ' ') {
            e.preventDefault()
            openPicker()
          }
        }}
        slotProps={{
          htmlInput: { readOnly: true, 'aria-haspopup': 'dialog', className: 'cursor-pointer' },
          input: {
            className: 'cursor-pointer',
            endAdornment: (
              <InputAdornment position="end">
                {allowAll && value ? (
                  <IconButton
                    size="small"
                    aria-label="Quitar filtro de producto"
                    onClick={(e) => {
                      e.stopPropagation()
                      onChange(null)
                    }}
                  >
                    <ClearIcon fontSize="small" />
                  </IconButton>
                ) : (
                  <SearchIcon fontSize="small" className="text-ink-soft" />
                )}
              </InputAdornment>
            ),
          },
        }}
        {...props}
      />
      {open && (
        <ProductPickerDialog
          onClose={() => setOpen(false)}
          onPick={(product) => {
            onChange(product)
            setOpen(false)
          }}
        />
      )}
    </>
  )
}

function ProductPickerDialog({ onClose, onPick }) {
  const [search, setSearch] = useState('')
  const debouncedSearch = useDebounced(search)
  const [category, setCategory] = useState('')
  const [sort, setSort] = useState('name')
  const pager = usePagination(10)
  // shortcut: las categorías salen de los primeros 200 productos; un endpoint de categorías si el catálogo crece.
  const catalog = useProductOptions()
  const categories = [...new Set(catalog.items.map((p) => p.category).filter(Boolean))].sort()

  const { data, loading, error, reload } = useApi(
    () =>
      productsApi.list({
        search: debouncedSearch || undefined,
        category: category || undefined,
        sort,
        ...pager.params,
      }),
    [debouncedSearch, category, sort, pager.page, pager.rowsPerPage],
  )
  const filter = (setter) => (next) => {
    setter(next)
    pager.reset()
  }

  const columns = [
    {
      key: 'name',
      header: 'Producto',
      render: (p) => (
        <div className="flex flex-col">
          <span className="font-medium text-ink">{p.name}</span>
          <span className="text-xs text-ink-soft">{p.category || 'Sin categoría'}</span>
        </div>
      ),
    },
    { key: 'stock_quantity', header: 'Stock', align: 'right', mono: true },
    { key: 'price', header: 'Precio', align: 'right', mono: true, hideOnMobile: true, render: (p) => formatCOP(p.price) },
    {
      key: 'pick',
      header: <span className="sr-only">Elegir</span>,
      align: 'right',
      render: (p) => (
        <Button size="small" variant="outlined" onClick={() => onPick(p)} aria-label={`Elegir ${p.name}`}>
          Elegir
        </Button>
      ),
    },
  ]

  return (
    <FormDialog title="Buscar producto" icon={<Inventory2OutlinedIcon />} onClose={onClose} maxWidth="sm">
      <div className="flex flex-wrap gap-3">
        <SearchField value={search} onChange={filter(setSearch)} autoFocus className="min-w-48 flex-1" />
        <SelectField
          size="small"
          label="Categoría"
          options={[['', 'Todas'], ...categories.map((c) => [c, c])]}
          value={category}
          onChange={filter(setCategory)}
          className="min-w-36"
        />
        <SelectField size="small" label="Orden" options={SORTS} value={sort} onChange={filter(setSort)} className="min-w-36" />
      </div>
      <DataTable
        bare
        label="Productos"
        columns={columns}
        rows={data?.items}
        loading={loading}
        error={error}
        onRetry={reload}
        pagination={{ ...pager, total: data?.total }}
        empty={<Empty title="Ningún producto coincide">Prueba con otro nombre o quita los filtros.</Empty>}
      />
    </FormDialog>
  )
}
