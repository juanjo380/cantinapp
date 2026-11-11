import PlaceIcon from '@mui/icons-material/PlaceOutlined'
import { useLocationScope } from '../../hooks/useLocationScope'
import SelectField from './SelectField'
import { Stamp } from './Stamp'

// Selector de sede para ventas y métricas. Sin sedes no se muestra; con sede asignada, solo un sello
// (el backend ignora cualquier otra sede que se pida).
export default function LocationFilter({ value, onChange, allLabel = 'Todas las sedes', ...props }) {
  const { locations, own: assigned } = useLocationScope()
  if (!locations.length) return null
  if (assigned) {
    return (
      <Stamp icon={<PlaceIcon sx={{ fontSize: '1.05rem' }} />}>
        {locations.find((l) => l.id === assigned)?.name ?? 'Tu sede'}
      </Stamp>
    )
  }
  return (
    <SelectField
      size="small"
      label="Sede"
      options={[['', allLabel], ...locations.map((l) => [l.id, l.name])]}
      value={value}
      onChange={onChange}
      className="min-w-44"
      {...props}
    />
  )
}
