import MenuItem from '@mui/material/MenuItem'
import TextField from '@mui/material/TextField'

// Select de MUI a partir de pares [valor, etiqueta]; el resto de props va al TextField.
export default function SelectField({ options, value, onChange, ...props }) {
  return (
    <TextField select value={value} onChange={(e) => onChange(e.target.value)} {...props}>
      {options.map(([optionValue, label]) => (
        <MenuItem key={optionValue} value={optionValue}>
          {label}
        </MenuItem>
      ))}
    </TextField>
  )
}
