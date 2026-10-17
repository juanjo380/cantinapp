import Alert from '@mui/material/Alert'
import Button from '@mui/material/Button'
import Tab from '@mui/material/Tab'
import Tabs from '@mui/material/Tabs'
import Table from '@mui/material/Table'
import TableBody from '@mui/material/TableBody'
import TableCell from '@mui/material/TableCell'
import TableContainer from '@mui/material/TableContainer'
import TableHead from '@mui/material/TableHead'
import TableRow from '@mui/material/TableRow'
import { useState } from 'react'
import { alertsApi, productsApi } from '../api/helper'
import PageHeader from '../components/ui/PageHeader'
import { Stamp } from '../components/ui/Stamp'
import { Empty, ErrorView, Loading } from '../components/ui/States'
import { useApi } from '../hooks/useApi'
import { formatDateTime, formatNumber } from '../utils/format'

export default function Alerts() {
  const [status, setStatus] = useState('PENDING')
  const [notice, setNotice] = useState(null)
  const [generating, setGenerating] = useState(false)

  const products = useApi(() => productsApi.list({ active_only: false, limit: 200, sort: 'name' }), [])
  const { data, loading, error, reload } = useApi(() => alertsApi.list({ status, limit: 50 }), [status])

  const nameById = new Map((products.data?.items ?? []).map((p) => [p.id, p.name]))
  const items = data?.items ?? []

  async function onGenerate() {
    setGenerating(true)
    setNotice(null)
    try {
      const result = await alertsApi.generate()
      setNotice({
        severity: 'success',
        text:
          result.created > 0
            ? `Se generaron ${result.created} alertas nuevas.`
            : 'No hay alertas nuevas: tu stock está bajo control.',
      })
      setStatus('PENDING')
      reload()
    } catch (err) {
      setNotice({ severity: 'error', text: err.message })
    } finally {
      setGenerating(false)
    }
  }

  async function onReview(id) {
    setNotice(null)
    try {
      await alertsApi.review(id)
      reload()
    } catch (err) {
      setNotice({ severity: 'error', text: err.message })
    }
  }

  return (
    <>
      <PageHeader
        title="Alertas"
        subtitle="El Sistema no vigila solo: genera las alertas cuando tú lo pides."
      >
        <Button variant="contained" onClick={onGenerate} disabled={generating}>
          {generating ? 'Actualizando…' : 'Actualizar alertas'}
        </Button>
      </PageHeader>

      {notice && (
        <Alert severity={notice.severity} className="mb-4" onClose={() => setNotice(null)}>
          {notice.text}
        </Alert>
      )}

      <Tabs
        value={status}
        onChange={(_, next) => setStatus(next)}
        className="mb-4 border-b border-line"
        aria-label="Estado de las alertas"
      >
        <Tab value="PENDING" label="Pendientes" />
        <Tab value="REVIEWED" label="Revisadas" />
      </Tabs>

      {loading && <Loading label="Cargando alertas…" />}
      {error && !loading && <ErrorView error={error} onRetry={reload} />}

      {!loading && !error && items.length === 0 && (
        <Empty title={status === 'PENDING' ? 'No hay alertas pendientes' : 'Todavía no has revisado alertas'}>
          {status === 'PENDING'
            ? 'Pulsa "Actualizar alertas" para revisar el stock y crear alertas de los productos bajos.'
            : 'Las alertas que marques como revisadas aparecerán aquí.'}
        </Empty>
      )}

      {!loading && !error && items.length > 0 && (
        <div className="surface overflow-hidden">
          <TableContainer>
            <Table size="small" aria-label="Alertas">
              <TableHead>
                <TableRow>
                  <TableCell>Producto</TableCell>
                  <TableCell align="right">Stock / mín.</TableCell>
                  <TableCell align="right">Demanda est.</TableCell>
                  <TableCell align="right">Sugerido</TableCell>
                  <TableCell>Generada</TableCell>
                  {status === 'PENDING' && <TableCell align="right">Acción</TableCell>}
                </TableRow>
              </TableHead>
              <TableBody>
                {items.map((alert) => (
                  <TableRow key={alert.id} hover>
                    <TableCell>{nameById.get(alert.product_id) ?? `Producto #${alert.product_id}`}</TableCell>
                    <TableCell align="right" className="font-mono">
                      {alert.current_stock} / {alert.min_stock}
                    </TableCell>
                    <TableCell align="right" className="font-mono">
                      {alert.estimated_demand != null ? formatNumber(alert.estimated_demand) : '—'}
                    </TableCell>
                    <TableCell align="right" className="font-mono">
                      {alert.recommended_quantity != null ? `${alert.recommended_quantity} u.` : '—'}
                    </TableCell>
                    <TableCell>{formatDateTime(alert.created_at)}</TableCell>
                    {status === 'PENDING' && (
                      <TableCell align="right">
                        <Button size="small" onClick={() => onReview(alert.id)}>
                          Marcar revisada
                        </Button>
                      </TableCell>
                    )}
                    {status === 'REVIEWED' && (
                      <TableCell align="right">
                        <Stamp tone="ok">Revisada</Stamp>
                      </TableCell>
                    )}
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        </div>
      )}
    </>
  )
}
