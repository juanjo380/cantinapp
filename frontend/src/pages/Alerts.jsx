import CheckCircleOutlineIcon from '@mui/icons-material/CheckCircleOutlined'
import NotificationsOffOutlinedIcon from '@mui/icons-material/NotificationsOffOutlined'
import RefreshIcon from '@mui/icons-material/Refresh'
import Button from '@mui/material/Button'
import Tab from '@mui/material/Tab'
import Tabs from '@mui/material/Tabs'
import { useState } from 'react'
import { alertsApi } from '../api/helper'
import DataTable, { RowAction } from '../components/ui/DataTable'
import PageHeader from '../components/ui/PageHeader'
import { Stamp } from '../components/ui/Stamp'
import { Empty, Notice } from '../components/ui/States'
import { useApi } from '../hooks/useApi'
import { useProductOptions } from '../hooks/useProductOptions'
import { formatDateTime, formatNumber } from '../utils/format'

export default function Alerts() {
  const [status, setStatus] = useState('PENDING')
  const [notice, setNotice] = useState(null)
  const [generating, setGenerating] = useState(false)

  const products = useProductOptions({ activeOnly: false })
  const { data, loading, error, reload } = useApi(() => alertsApi.list({ status, limit: 50 }), [status])

  const nameById = new Map(products.items.map((p) => [p.id, p.name]))
  const isPending = status === 'PENDING'

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

  const columns = [
    { key: 'product_id', header: 'Producto', render: (a) => nameById.get(a.product_id) ?? (products.loading ? '…' : 'Producto desconocido') },
    { key: 'stock', header: 'Stock / mín.', align: 'right', mono: true, render: (a) => `${a.current_stock} / ${a.min_stock}` },
    {
      key: 'estimated_demand',
      header: 'Demanda est.',
      align: 'right',
      mono: true,
      hideOnMobile: true,
      render: (a) => (a.estimated_demand != null ? formatNumber(a.estimated_demand) : '—'),
    },
    {
      key: 'recommended_quantity',
      header: 'Sugerido',
      align: 'right',
      mono: true,
      render: (a) => (a.recommended_quantity != null ? `${a.recommended_quantity} u.` : '—'),
    },
    { key: 'created_at', header: 'Generada', hideOnMobile: true, render: (a) => formatDateTime(a.created_at) },
    {
      key: 'action',
      header: isPending ? 'Acción' : 'Estado',
      align: 'right',
      render: (a) =>
        isPending ? (
          <RowAction
            title="Marcar revisada"
            color="success"
            icon={<CheckCircleOutlineIcon fontSize="small" />}
            onClick={() => onReview(a.id)}
          />
        ) : (
          <Stamp tone="ok">Revisada</Stamp>
        ),
    },
  ]

  return (
    <>
      <PageHeader title="Alertas" subtitle="El Sistema no vigila solo: genera las alertas cuando tú lo pides.">
        <Button variant="contained" startIcon={<RefreshIcon />} onClick={onGenerate} disabled={generating}>
          {generating ? 'Actualizando…' : 'Actualizar alertas'}
        </Button>
      </PageHeader>

      <Notice notice={notice} onClose={() => setNotice(null)} />

      <Tabs
        value={status}
        onChange={(_, next) => setStatus(next)}
        className="mb-4 border-b border-line"
        aria-label="Estado de las alertas"
      >
        <Tab value="PENDING" label="Pendientes" />
        <Tab value="REVIEWED" label="Revisadas" />
      </Tabs>

      <DataTable
        label="Alertas"
        columns={columns}
        rows={data?.items}
        loading={loading}
        error={error}
        onRetry={reload}
        empty={
          <Empty
            icon={<NotificationsOffOutlinedIcon />}
            title={isPending ? 'No hay alertas pendientes' : 'Todavía no has revisado alertas'}
          >
            {isPending
              ? 'Pulsa "Actualizar alertas" para revisar el stock y crear alertas de los productos bajos.'
              : 'Las alertas que marques como revisadas aparecerán aquí.'}
          </Empty>
        }
      />
    </>
  )
}
