import { LineChart } from '@mui/x-charts/LineChart'
import { useTheme } from '@mui/material/styles'
import MenuItem from '@mui/material/MenuItem'
import TextField from '@mui/material/TextField'
import ToggleButton from '@mui/material/ToggleButton'
import ToggleButtonGroup from '@mui/material/ToggleButtonGroup'
import { useState } from 'react'
import { analyticsApi, productsApi } from '../api/helper'
import PageHeader from '../components/ui/PageHeader'
import { Empty, ErrorView, Loading } from '../components/ui/States'
import { useApi } from '../hooks/useApi'
import { daysAgoISO, formatCOP, formatNumber, todayISO } from '../utils/format'

const PERIODS = [
  ['daily', 'Diario'],
  ['weekly', 'Semanal'],
  ['monthly', 'Mensual'],
  ['yearly', 'Anual'],
]

export default function Analytics() {
  const theme = useTheme()
  const [period, setPeriod] = useState('daily')
  const [dateFrom, setDateFrom] = useState(daysAgoISO(30))
  const [dateTo, setDateTo] = useState(todayISO())
  const [productId, setProductId] = useState('')
  const [metric, setMetric] = useState('units')

  const products = useApi(() => productsApi.list({ active_only: true, limit: 200, sort: 'name' }), [])
  const series = useApi(
    () =>
      analyticsApi.sales({
        period,
        date_from: dateFrom || undefined,
        date_to: dateTo || undefined,
        product_id: productId || undefined,
      }),
    [period, dateFrom, dateTo, productId],
  )
  const top = useApi(
    () => analyticsApi.topProducts({ order: 'top', limit: 10, date_from: dateFrom || undefined, date_to: dateTo || undefined }),
    [dateFrom, dateTo],
  )
  const bottom = useApi(
    () => analyticsApi.topProducts({ order: 'bottom', limit: 10, date_from: dateFrom || undefined, date_to: dateTo || undefined }),
    [dateFrom, dateTo],
  )

  const labels = (series.data?.series ?? []).map((point) => point.period)
  const values = (series.data?.series ?? []).map((point) =>
    metric === 'units' ? point.units : point.revenue,
  )
  const productOptions = products.data?.items ?? []

  return (
    <>
      <PageHeader title="Análisis" subtitle="Cómo se mueven tus ventas en el período." />

      <div className="filter-row items-end">
        <TextField size="small" select label="Período" value={period} onChange={(e) => setPeriod(e.target.value)} className="min-w-36">
          {PERIODS.map(([value, label]) => (
            <MenuItem key={value} value={value}>
              {label}
            </MenuItem>
          ))}
        </TextField>
        <TextField size="small" type="date" label="Desde" value={dateFrom} onChange={(e) => setDateFrom(e.target.value)} InputLabelProps={{ shrink: true }} />
        <TextField size="small" type="date" label="Hasta" value={dateTo} onChange={(e) => setDateTo(e.target.value)} InputLabelProps={{ shrink: true }} />
        <TextField size="small" select label="Producto" value={productId} onChange={(e) => setProductId(e.target.value)} className="min-w-48">
          <MenuItem value="">Todos</MenuItem>
          {productOptions.map((p) => (
            <MenuItem key={p.id} value={p.id}>
              {p.name}
            </MenuItem>
          ))}
        </TextField>
        <ToggleButtonGroup
          size="small"
          exclusive
          value={metric}
          onChange={(_, next) => next && setMetric(next)}
          aria-label="Métrica"
        >
          <ToggleButton value="units">Unidades</ToggleButton>
          <ToggleButton value="revenue">Dinero</ToggleButton>
        </ToggleButtonGroup>
      </div>

      <section aria-label="Tendencia de ventas" className="surface p-5">
        {series.loading && <Loading label="Calculando tendencia…" />}
        {series.error && !series.loading && <ErrorView error={series.error} onRetry={series.reload} />}
        {!series.loading && !series.error && labels.length === 0 && (
          <Empty title="Sin ventas en este rango">
            Ajusta las fechas o carga ventas en la sección Ventas.
          </Empty>
        )}
        {!series.loading && !series.error && labels.length > 0 && (
          <LineChart
            height={320}
            xAxis={[{ scaleType: 'band', data: labels, valueFormatter: (value) => value }]}
            series={[
              {
                data: values,
                label: metric === 'units' ? 'Unidades' : 'Ingresos (COP)',
                color: theme.palette.primary.main,
                area: metric === 'units',
                curve: 'monotoneX',
                valueFormatter: (value) =>
                  metric === 'units' ? formatNumber(value) : formatCOP(value),
              },
            ]}
            margin={{ left: 70, right: 16, top: 24, bottom: 40 }}
          />
        )}
      </section>

      <div className="mt-6 grid grid-cols-1 gap-6 lg:grid-cols-2">
        <Ranking title="Más vendidos" query={top} />
        <Ranking title="Menos vendidos" query={bottom} />
      </div>
    </>
  )
}

function Ranking({ title, query }) {
  const items = query.data?.items ?? []
  return (
    <section aria-label={title} className="surface p-5">
      <h2 className="mb-3 text-base font-semibold text-ink">{title}</h2>
      {query.loading && <Loading label="Cargando ranking…" />}
      {query.error && !query.loading && <ErrorView error={query.error} onRetry={query.reload} />}
      {!query.loading && !query.error && items.length === 0 && (
        <p className="py-6 text-center text-sm text-ink-soft">Sin datos en el rango.</p>
      )}
      {!query.loading && !query.error && items.length > 0 && (
        <ol className="flex flex-col divide-y divide-line">
          {items.map((item, index) => (
            <li key={item.product_id} className="flex items-center gap-3 py-2">
              <span className="w-6 text-right font-mono text-sm text-ink-soft">{index + 1}</span>
              <span className="min-w-0 flex-1 truncate text-sm text-ink">{item.name}</span>
              <span className="font-mono text-sm text-ink-soft">{formatNumber(item.units)} u.</span>
              <span className="w-24 text-right font-mono text-sm">{formatCOP(item.revenue)}</span>
            </li>
          ))}
        </ol>
      )}
    </section>
  )
}
