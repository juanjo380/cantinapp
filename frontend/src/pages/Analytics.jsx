import { LineChart } from '@mui/x-charts/LineChart'
import { useTheme } from '@mui/material/styles'
import TextField from '@mui/material/TextField'
import ToggleButton from '@mui/material/ToggleButton'
import ToggleButtonGroup from '@mui/material/ToggleButtonGroup'
import { useState } from 'react'
import { analyticsApi } from '../api/helper'
import PageHeader from '../components/ui/PageHeader'
import Section from '../components/ui/Section'
import SelectField from '../components/ui/SelectField'
import DataTable from '../components/ui/DataTable'
import { Stamp } from '../components/ui/Stamp'
import { Empty, ErrorView, Loading } from '../components/ui/States'
import { useApi } from '../hooks/useApi'
import { useProductOptions } from '../hooks/useProductOptions'
import { daysAgoISO, formatCOP, formatNumber, formatPercent, todayISO } from '../utils/format'

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

  const products = useProductOptions()
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
  const classification = useApi(
    () => analyticsApi.classification({ date_from: dateFrom || undefined, date_to: dateTo || undefined }),
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

  return (
    <>
      <PageHeader title="Análisis" subtitle="Cómo se mueven tus ventas en el período." />

      <div className="filter-row items-end">
        <SelectField size="small" label="Período" options={PERIODS} value={period} onChange={setPeriod} className="min-w-36" />
        <TextField size="small" type="date" label="Desde" value={dateFrom} onChange={(e) => setDateFrom(e.target.value)} slotProps={{ inputLabel: { shrink: true } }} />
        <TextField size="small" type="date" label="Hasta" value={dateTo} onChange={(e) => setDateTo(e.target.value)} slotProps={{ inputLabel: { shrink: true } }} />
        <SelectField
          size="small"
          label="Producto"
          options={[['', 'Todos'], ...products.items.map((p) => [p.id, p.name])]}
          value={productId}
          onChange={setProductId}
          className="min-w-48"
        />
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

      <Section label="Tendencia de ventas">
        {series.loading && <Loading variant="chart" label="Calculando tendencia…" />}
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
      </Section>

      <div className="mt-6">
        <Classification query={classification} />
      </div>

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
    <Section title={title}>
      {query.loading && <Loading variant="list" rows={6} label="Cargando ranking…" />}
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
    </Section>
  )
}

const ABC = {
  A: { tone: 'ok', label: 'A · Clave' },
  B: { tone: 'warn', label: 'B · Importante' },
  C: { tone: 'neutral', label: 'C · Menor' },
}

function rankChange(row) {
  if (row.previous_rank == null) return <span className="text-ink-soft">Nuevo</span>
  const diff = row.previous_rank - row.rank
  if (diff === 0) return <span className="text-ink-soft">=</span>
  return (
    <span className={diff > 0 ? 'text-ok' : 'text-crit'} aria-label={diff > 0 ? `Subió ${diff}` : `Bajó ${-diff}`}>
      {diff > 0 ? `▲ ${diff}` : `▼ ${-diff}`}
    </span>
  )
}

const CLASSIFICATION_COLUMNS = [
  { key: 'rank', header: '#', align: 'right', mono: true },
  { key: 'name', header: 'Producto' },
  { key: 'abc', header: 'Clase', render: (row) => <Stamp tone={ABC[row.abc].tone}>{ABC[row.abc].label}</Stamp> },
  { key: 'revenue', header: 'Ingresos', align: 'right', mono: true, render: (row) => formatCOP(row.revenue) },
  { key: 'share', header: '% del total', align: 'right', mono: true, render: (row) => formatPercent(row.share) },
  { key: 'units', header: 'Unidades', align: 'right', mono: true, hideOnMobile: true, render: (row) => formatNumber(row.units) },
  { key: 'previous_rank', header: 'Puesto', align: 'right', mono: true, hideOnMobile: true, render: rankChange },
]

function Classification({ query }) {
  const items = query.data?.items ?? []
  const classA = items.filter((item) => item.abc === 'A').length
  return (
    <Section title="Clasificación de productos" label="Clasificación ABC de productos">
      {items.length > 0 && (
        <p className="mb-4 text-sm text-ink-soft">
          <strong className="text-ink">
            {classA} de {items.length} productos
          </strong>{' '}
          hacen el 80 % de tus ingresos: son los que nunca deben faltar. La columna Puesto compara con el período
          anterior de la misma duración.
        </p>
      )}
      <DataTable
        bare
        label="Clasificación"
        columns={CLASSIFICATION_COLUMNS}
        rows={items}
        rowKey="product_id"
        loading={query.loading}
        error={query.error}
        onRetry={query.reload}
        maxHeight={420}
        empty={<p className="py-6 text-center text-sm text-ink-soft">Sin ventas en el rango.</p>}
      />
    </Section>
  )
}
