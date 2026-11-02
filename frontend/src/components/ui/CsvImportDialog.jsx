import UploadFileIcon from '@mui/icons-material/UploadFile'
import Alert from '@mui/material/Alert'
import Button from '@mui/material/Button'
import { useState } from 'react'
import DataTable from './DataTable'
import FormDialog from './FormDialog'

const ERROR_COLUMNS = [
  { key: 'row', header: 'Fila', mono: true },
  { key: 'field', header: 'Campo' },
  { key: 'message', header: 'Mensaje' },
]

// Carga de CSV con resumen y errores por fila. `upload(file)` llama al endpoint; `children` va
// antes del selector (ayuda, opciones) y `next` se muestra tras una carga (p. ej. un enlace).
export default function CsvImportDialog({ title, upload, onClose, onDone, next, children }) {
  const [file, setFile] = useState(null)
  const [result, setResult] = useState(null)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  async function onUpload() {
    if (!file) {
      setError('Elige un archivo CSV.')
      return
    }
    setLoading(true)
    setError('')
    try {
      const outcome = await upload(file)
      setResult(outcome)
      onDone(outcome)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <FormDialog
      title={title}
      icon={<UploadFileIcon />}
      maxWidth="md"
      onClose={onClose}
      onSubmit={onUpload}
      submitLabel="Cargar CSV"
      submittingLabel="Subiendo…"
      submitting={loading}
      cancelLabel={result ? 'Cerrar' : 'Cancelar'}
      error={error}
    >
      {children}
      <Button component="label" variant="outlined" startIcon={<UploadFileIcon />} className="self-start">
        {file ? file.name : 'Elegir archivo CSV'}
        <input type="file" hidden accept=".csv,text/csv" onChange={(e) => setFile(e.target.files?.[0] ?? null)} />
      </Button>
      <p className="text-xs text-ink-soft">
        Sirve el CSV de Excel (separado por comas o punto y coma) y precios con coma decimal. Máximo 5 MB.
      </p>

      {result && (
        <div className="flex flex-col gap-3">
          <Alert severity={result.error_rows > 0 ? 'warning' : 'success'}>
            {result.imported_rows} de {result.total_rows} filas importadas; {result.error_rows} con error.
          </Alert>
          {result.errors?.length > 0 && (
            <DataTable label="Errores del CSV" columns={ERROR_COLUMNS} rows={result.errors} maxHeight={256} />
          )}
          {next}
        </div>
      )}
    </FormDialog>
  )
}
