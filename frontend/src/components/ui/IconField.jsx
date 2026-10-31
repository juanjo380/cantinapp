import VisibilityIcon from '@mui/icons-material/VisibilityOutlined'
import VisibilityOffIcon from '@mui/icons-material/VisibilityOffOutlined'
import IconButton from '@mui/material/IconButton'
import InputAdornment from '@mui/material/InputAdornment'
import TextField from '@mui/material/TextField'
import { useState } from 'react'

// TextField con icono a la izquierda y, opcionalmente, un elemento a la derecha.
export default function IconField({ icon, end, ...props }) {
  return (
    <TextField
      {...props}
      slotProps={{
        ...props.slotProps,
        input: {
          startAdornment: icon && <InputAdornment position="start">{icon}</InputAdornment>,
          endAdornment: end && <InputAdornment position="end">{end}</InputAdornment>,
        },
      }}
    />
  )
}

// Contraseña con botón para mostrarla u ocultarla.
export function PasswordField(props) {
  const [visible, setVisible] = useState(false)
  return (
    <IconField
      {...props}
      type={visible ? 'text' : 'password'}
      end={
        <IconButton
          size="small"
          edge="end"
          onClick={() => setVisible((v) => !v)}
          aria-label={visible ? 'Ocultar contraseña' : 'Mostrar contraseña'}
        >
          {visible ? <VisibilityOffIcon fontSize="small" /> : <VisibilityIcon fontSize="small" />}
        </IconButton>
      }
    />
  )
}
