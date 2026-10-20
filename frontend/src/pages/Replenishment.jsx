import Button from '@mui/material/Button'
import MenuItem from '@mui/material/MenuItem'
import TextField from '@mui/material/TextField'
import { useTheme } from '@mui/material/styles'
import { LineChart } from '@mui/x-charts/LineChart'
import { useEffect, useState } from 'react'
import { Link as RouterLink } from 'react-router-dom'
import { analyticsApi, forecastingApi, productsApi, recommendationsApi } from '../api/helper'
import PageHeader from '../components/ui/PageHeader'
import { ProvenanceStamp, UrgencyStamp } from '../components/ui/Stamp'
import { Empty, ErrorView, Loading } from '../components/ui/States'
import { useApi } from '../hooks/useApi'
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

  const products = useApi(() => productsApi.list({ active_only: true, limit: 200, sort: 'name' }), [])
  const productOptions = products.data?.items ?? []

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
        <TextField
          size="small"
          select
          label="Producto"
          value={productId}
          onChange={(e) => setProductId(e.target.value)}
          className="min-w-56"
        >
          <MenuItem value="">Elige un producto</MenuItem>
          {productOptions.map((p) => (
            <MenuItem key={p.id} value={p.id}>
              {p.name}
            </MenuItem>
          ))}
        </TextField>
        <TextField
          size="small"
          type="number"
          label="Días a predecir"
          value={forecastDays}
          onChange={(e) => setForecastDays(e.target.value)}
          InputLabelProps={{ shrink: true }}
          className="w-36"
          inputProps={{ min: 1, max: 365 }}
        />
        <TextField size="small" select label="Modelo" value={model} onChange={(e) => setModel(e.target.value)} className="min-w-44">
          {MODELS.map(([value, label]) => (
            <MenuItem key={value} value={value}>
              {label}
            </MenuItem>
          ))}
        </TextField>
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
        <ForecastView
          forecast={result.forecast}
          recommendation={result.recommendation}
          history={result.history}
          color={theme.palette.primary.main}
          accent={theme.palette.warning.main}
        />
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
      <section aria-label="Histórico contra predicción" className="surface p-5">
        <div className="mb-3 flex flex-wrap items-center justify-between gap-2">
          <h2 className="text-base font-semibold text-ink">Histórico vs. predicción</h2>
          <div className="flex flex-wrap items-center gap-2">
            <span className="font-mono text-stamp tracking-stamp uppercase text-ink-soft">
              Modelo: {forecast.model_type === 'LINEAR_REGRESSION' ? 'Regresión lineal' : 'Promedio móvil'} ·
              Confianza {formatPercent(forecast.confidence)}
            </span>
          </div>
        </div>
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
      </section>

      <section aria-label="Predicción" className="grid grid-cols-1 gap-4 sm:grid-cols-3">
        <Metric label="Demanda estimada" value={`${forecast.predicted_demand} u.`} hint={`Próximos ${forecast.forecast_days} días`} />
        <Metric label="Historial usado" value={`${forecast.history_days} días`} hint="Base de la predicción" />
        <Metric label="Confianza" value={formatPercent(forecast.confidence)} hint="0 % a 100 %" />
      </section>

      <section aria-label="Recomendación de compra" className="surface p-5">
        <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
          <h2 className="text-base font-semibold text-ink">Recomendación de compra</h2>
          <UrgencyStamp urgency={recommendation.urgency} />
        </div>

        <p className="mb-4 text-sm text-ink-soft">{recommendation.justification}</p>

        <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
          <Metric label="Comprar" value={`${recommendation.suggested_quantity} u.`} strong />
          <Metric label="Cobertura" value={`${recommendation.coverage_days} días`} />
          <Metric label="Stock actual" value={`${recommendation.current_stock} u.`} />
          <Metric label="Stock mínimo" value={`${recommendation.min_stock} u.`} />
        </div>

        <div className="mt-4 flex flex-wrap items-center gap-2">
          <span className="font-mono text-stamp tracking-stamp uppercase text-ink-soft">
            Abastecimiento: {recommendation.lead_time_days} días
          </span>
          <ProvenanceStamp date={recommendation.created_at} />
        </div>
      </section>
    </div>
  )
}

function Metric({ label, value, hint, strong }) {
  return (
    <div className="surface-inset p-4">
      <p className="font-mono text-stamp tracking-stamp uppercase text-ink-soft">{label}</p>
      <p className={`mt-1 font-mono ${strong ? 'text-2xl font-bold text-brand' : 'text-lg font-semibold text-ink'}`}>
        {value}
      </p>
      {hint && <p className="text-xs text-ink-soft">{hint}</p>}
    </div>
  )
}
