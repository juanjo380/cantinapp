import SearchIcon from '@mui/icons-material/Search'
import IconField from './IconField'

export default function SearchField({ value, onChange, label = 'Buscar', ...props }) {
  return (
    <IconField
      size="small"
      label={label}
      value={value}
      onChange={(e) => onChange(e.target.value)}
      icon={<SearchIcon fontSize="small" />}
      {...props}
    />
  )
}
