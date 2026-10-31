import RefreshIcon from '@mui/icons-material/Refresh'
import Button from '@mui/material/Button'
import TextField from '@mui/material/TextField'
import { useTheme } from '@mui/material/styles'
import { LineChart } from '@mui/x-charts/LineChart'
import { useEffect, useState } from 'react'
import { Link as RouterLink } from 'react-router-dom'
import { analyticsApi, forecastingApi, recommendationsApi } from '../api/helper'
import DataTable from '../components/ui/DataTable'
import PageHeader from '../components/ui/PageHeader'
import Section from '../components/ui/Section'
import SelectField from '../components/ui/SelectField'
import StatCard from '../components/ui/StatCard'
import { ProvenanceStamp, UrgencyStamp } from '../components/ui/Stamp'
import { Empty, ErrorView, Loading, Notice } from '../components/ui/States'
import { useApi } from '../hooks/useApi'
import { useProductOptions } from '../hooks/useProductOptions'
import { daysAgoISO, formatPercent, todayISO } from '../utils/format'

const MODELS = [
  ['MOVING_AVERAGE', 'Promedio móvil'],
  ['LINEAR_REGRESSION', 'Regresión lineal'],
]

export default function Replenishment() {
  const theme = useTheme()
  const [productId, setProductId] = useState('')
  const [forecastDays, setForecastDays] = useState('30')
  const [model, setModel] = useState('MOVING_AVERAGE')
  const [result, setResult] = useState({ status: 'idle' })

  const products = useProductOptions()
  const productOptions = products.items

  useEffect(() => {
    if (!productId) {
      setResult({ status: 'idle' })
      return
    }
    let alive = true
    setResult({ status: 'loading' })
    ;(async () => {
      try {
        const forecast = await forecastingApi.create({
          product_id: productId,
          forecast_days: Number(forecastDays),
          model,
        })
        const [recommendation, history] = await Promise.all([
          recommendationsApi.create({
            product_id: productId,
            forecast_days: Number(forecastDays),
          }),
          analyticsApi.sales({
            product_id: productId,
            period: 'daily',
            date_from: daysAgoISO(Math.min(365, (forecast.history_days || 30) + 5)),
            date_to: todayISO(),
          }),
        ])
        if (alive) setResult({ status: 'ready', forecast, recommendation, history })
      } catch (err) {
        if (!alive) return
        setResult({ status: err.status === 422 ? 'insufficient' : 'error', error: err })
      }
    })()
    return () => {
      alive = false
    }
  }, [productId, forecastDays, model])

  return (
    <>
      <PageHeader
        title="Reabastecimiento"
        subtitle="Elige un producto: el Sistema predice la demanda y recomienda cuánto comprar."
      />

      <div className="filter-row items-end">
        <SelectField
          size="small"
          label="Producto"
          options={[['', 'Elige un producto'], ...productOptions.map((p) => [p.id, p.name])]}
          value={productId}
          onChange={setProductId}
          className="min-w-56"
        />
        <TextField
          size="small"
          type="number"
          label="Días a predecir"
          value={forecastDays}
          onChange={(e) => setForecastDays(e.target.value)}
          slotProps={{ inputLabel: { shrink: true }, htmlInput: { min: 1, max: 365 } }}
          className="w-36"
        />
        <SelectField size="small" label="Modelo" options={MODELS} value={model} onChange={setModel} className="min-w-44" />
      </div>

      {products.loading && <Loading label="Cargando productos…" />}
      {products.error && !products.loading && <ErrorView error={products.error} onRetry={products.reload} />}

      {!products.loading && !products.error && productOptions.length === 0 && (
        <Empty
          title="Aún no tienes productos"
          action={
            <Button component={RouterLink} to="/productos" variant="contained">
              Ir a Productos
            </Button>
          }
        >
          Registra productos y carga ventas para poder predecir la demanda.
        </Empty>
      )}

      {result.status === 'idle' && productOptions.length > 0 && (
        <Empty title="Elige un producto arriba">
          El Sistema usará su historial de ventas para predecir la demanda y recomendar una compra.
        </Empty>
      )}

      {result.status === 'loading' && <Loading label="Analizando historial…" />}
      {result.status === 'error' && <ErrorView error={result.error} />}
      {result.status === 'insufficient' && (
        <Empty
          title="Faltan datos para predecir"
          action={
            <Button component={RouterLink} to="/ventas" variant="contained">
              Cargar historial por CSV
            </Button>
          }
        >
          El pronóstico necesita al menos 30 días de historial de ventas. Carga tu historial en Ventas
          y vuelve a intentarlo.
        </Empty>
      )}

      {result.status === 'ready' && (
        <div className="flex flex-col gap-6">
          <ForecastView
            forecast={result.forecast}
            recommendation={result.recommendation}
            history={result.history}
            color={theme.palette.primary.main}
            accent={theme.palette.warning.main}
          />
          <CoOccurrenceView productId={productId} />
        </div>
      )}
    </>
  )
}

function ForecastView({ forecast, recommendation, history, color, accent }) {
  const historyPoints = history?.series ?? []
  const forecastPoints = forecast.daily_prediction ?? []
  const historyLabels = historyPoints.map((point) => point.period)
  const forecastLabels = forecastPoints.map((point) => point.date)
  const labels = [...historyLabels, ...forecastLabels]
  const historyData = [...historyPoints.map((point) => point.units), ...forecastLabels.map(() => null)]
  const forecastData = [...historyLabels.map(() => null), ...forecastPoints.map((point) => point.value)]

  return (
    <div className="flex flex-col gap-6">
      <Section
        title="Histórico vs. predicción"
        label="Histórico contra predicción"
        actions={
          <span className="font-mono text-stamp tracking-stamp uppercase text-ink-soft">
            Modelo: {forecast.model_type === 'LINEAR_REGRESSION' ? 'Regresión lineal' : 'Promedio móvil'} ·
            Confianza {formatPercent(forecast.confidence)}
          </span>
        }
      >
        {labels.length === 0 ? (
          <Empty title="Sin datos para graficar">No hay serie diaria disponible.</Empty>
        ) : (
          <LineChart
            height={320}
            xAxis={[{ scaleType: 'band', data: labels }]}
            series={[
              { data: historyData, label: 'Histórico (unidades)', color, curve: 'monotoneX' },
              { data: forecastData, label: 'Predicción (unidades)', color: accent, curve: 'monotoneX' },
            ]}
            margin={{ left: 56, right: 16, top: 24, bottom: 40 }}
          />
        )}
      </Section>

      <section aria-label="Predicción" className="grid grid-cols-1 gap-4 sm:grid-cols-3">
        <StatCard variant="inset" label="Demanda estimada" value={`${forecast.predicted_demand} u.`} hint={`Próximos ${forecast.forecast_days} días`} />
        <StatCard variant="inset" label="Historial usado" value={`${forecast.history_days} días`} hint="Base de la predicción" />
        <StatCard variant="inset" label="Confianza" value={formatPercent(forecast.confidence)} hint="0 % a 100 %" />
      </section>

      <Section title="Recomendación de compra" actions={<UrgencyStamp urgency={recommendation.urgency} />}>

        <p className="mb-4 text-sm text-ink-soft">{recommendation.justification}</p>

        <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
          <StatCard variant="inset" label="Comprar" value={`${recommendation.suggested_quantity} u.`} strong />
          <StatCard variant="inset" label="Cobertura" value={`${recommendation.coverage_days} días`} />
          <StatCard variant="inset" label="Stock actual" value={`${recommendation.current_stock} u.`} />
          <StatCard variant="inset" label="Stock mínimo" value={`${recommendation.min_stock} u.`} />
        </div>

        <div className="mt-4 flex flex-wrap items-center gap-2">
          <span className="font-mono text-stamp tracking-stamp uppercase text-ink-soft">
            Abastecimiento: {recommendation.lead_time_days} días
          </span>
          <ProvenanceStamp date={recommendation.created_at} />
        </div>
      </Section>
    </div>
  )
}

const COOCCURRENCE_COLUMNS = [
  { key: 'related_product_name', header: 'Producto' },
  { key: 'score', header: 'Probabilidad', align: 'right', mono: true, render: (row) => formatPercent(row.score) },
  {
    key: 'hits',
    header: 'Coincidencias',
    align: 'right',
    mono: true,
    hideOnMobile: true,
    render: (row) => `${row.hits} de ${row.peaks} picos`,
  },
]

function CoOccurrenceView({ productId }) {
  const [notice, setNotice] = useState(null)
  const [recomputing, setRecomputing] = useState(false)
  const { data, loading, error, reload } = useApi(
    () => recommendationsApi.cooccurrence({ product_id: productId }),
    [productId],
  )
  const items = data?.items ?? []

  async function onRecompute() {
    setRecomputing(true)
    setNotice(null)
    try {
      await recommendationsApi.recomputeCooccurrence()
      setNotice({ severity: 'info', text: 'Recalculando con todo tu historial. Los resultados se actualizan en unos segundos.' })
      // shortcut: el recálculo corre en segundo plano sin estado consultable; si tarda más, pasar a polling
      setTimeout(reload, 4000)
    } catch (err) {
      setNotice({ severity: 'error', text: err.message })
    } finally {
      setRecomputing(false)
    }
  }

  return (
    <Section
      title="Productos que suben después"
      label="Productos asociados por co-ocurrencia"
      actions={
        <>
          {items.length > 0 && <ProvenanceStamp date={items[0].computed_at} />}
          <Button size="small" variant="outlined" startIcon={<RefreshIcon />} onClick={onRecompute} disabled={recomputing}>
            {recomputing ? 'Recalculando…' : 'Recalcular'}
          </Button>
        </>
      }
    >
      <p className="mb-4 text-sm text-ink-soft">
        Cuando este producto tiene un pico de ventas, estos productos suelen vender más de lo normal en los 3 días
        siguientes. Considera reforzar su stock.
      </p>
      <Notice notice={notice} onClose={() => setNotice(null)} />
      <DataTable
        bare
        label="Productos asociados"
        columns={COOCCURRENCE_COLUMNS}
        rows={items}
        rowKey="related_product_id"
        loading={loading}
        error={error}
        onRetry={reload}
        empty={
          <Empty title="Sin productos asociados">
            Ningún producto sube de forma consistente tras los picos de este, o aún no se ha calculado. Pulsa
            Recalcular para analizar tu historial.
          </Empty>
        }
      />
    </Section>
  )
}
