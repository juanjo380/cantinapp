import Alert from '@mui/material/Alert'
import Button from '@mui/material/Button'
import Dialog from '@mui/material/Dialog'
import DialogActions from '@mui/material/DialogActions'
import DialogContent from '@mui/material/DialogContent'
import DialogTitle from '@mui/material/DialogTitle'
import IconButton from '@mui/material/IconButton'
import CloseIcon from '@mui/icons-material/Close'

// Modal estándar: título con icono, error del servidor, contenido y acciones Cancelar/Enviar.
// Sin `onSubmit` solo muestra "Cerrar".
export default function FormDialog({
  title,
  icon,
  onClose,
  onSubmit,
  submitLabel = 'Guardar',
  submittingLabel = 'Guardando…',
  submitting = false,
  error,
  maxWidth = 'xs',
  cancelLabel = 'Cancelar',
  children,
}) {
  return (
    <Dialog open onClose={onClose} fullWidth maxWidth={maxWidth}>
      <DialogTitle className="flex items-center gap-2 pr-12">
        {icon && <span className="flex text-brand" aria-hidden="true">{icon}</span>}
        {title}
        <IconButton aria-label="Cerrar" onClick={onClose} size="small" sx={{ position: 'absolute', right: 12, top: 14 }}>
          <CloseIcon fontSize="small" />
        </IconButton>
      </DialogTitle>
      <DialogContent className="flex flex-col gap-4 pt-2">
        {error && <Alert severity="error">{error}</Alert>}
        {children}
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose}>{onSubmit ? cancelLabel : 'Cerrar'}</Button>
        {onSubmit && (
          <Button variant="contained" onClick={onSubmit} disabled={submitting}>
            {submitting ? submittingLabel : submitLabel}
          </Button>
        )}
      </DialogActions>
    </Dialog>
  )
}
