import ArrowBackIcon from '@mui/icons-material/ArrowBack'
import RefreshIcon from '@mui/icons-material/Refresh'
import Button from '@mui/material/Button'
import { useTheme } from '@mui/material/styles'
import { LineChart } from '@mui/x-charts/LineChart'
import { useState } from 'react'
import { Link as RouterLink } from 'react-router-dom'
import { analyticsApi, forecastingApi, recommendationsApi } from '../api/helper'
import DataTable from '../components/ui/DataTable'
import DemoData from '../components/ui/DemoData'
import PageHeader from '../components/ui/PageHeader'
import Section from '../components/ui/Section'
import StatCard from '../components/ui/StatCard'
import { ProvenanceStamp, Stamp, UrgencyStamp } from '../components/ui/Stamp'
import { Empty, ErrorView, Loading, Notice } from '../components/ui/States'
import { useApi } from '../hooks/useApi'
import { daysAgoISO, formatDate, formatNumber, formatPercent, todayISO } from '../utils/format'

// El modelo lo elige el Sistema (AUTO); al usuario solo se le explica en palabras qué patrón encontró.
const MODEL_EXPLAIN = {
  SEASONAL_WEEKLY: 'Tus ventas cambian según el día de la semana, y lo tuvimos en cuenta.',
  MOVING_AVERAGE: 'Tus ventas son estables, así que usamos tu promedio de los últimos días.',
  LINEAR_REGRESSION: 'Tus ventas vienen cambiando de forma sostenida, y seguimos esa tendencia.',
}

function reliability(confidence) {
  if (confidence == null) return { label: 'Aún sin medir', hint: 'Falta historial para comprobarla' }
  const hint = `Acertó ${formatPercent(confidence)} en las últimas 2 semanas`
  if (confidence >= 0.75) return { label: 'Alta', hint }
  if (confidence >= 0.5) return { label: 'Media', hint }
  return { label: 'Baja', hint: 'Tus ventas varían mucho: revisa antes de comprar' }
}

const coverageText = (days) => (days == null ? 'Sin ventas recientes' : `${formatNumber(Math.floor(days))} días`)
const buyText = (qty) => (qty > 0 ? `${formatNumber(qty)} u.` : 'Nada por ahora')

export default function Replenishment() {
  const plan = useApi(() => recommendationsApi.plan(), [])
  const [selected, setSelected] = useState(null)
  const items = plan.data?.items ?? []
  const pending = plan.data?.pending ?? []

  if (selected) return <ProductDetail item={selected} onBack={() => setSelected(null)} />

  const count = (urgency) => items.filter((i) => i.urgency === urgency).length
  const columns = [
    {
      key: 'name',
      header: 'Producto',
      render: (row) => (
        <span className="flex flex-col">
          <span className="text-ink">{row.name}</span>
          {row.category && <span className="text-xs text-ink-soft">{row.category}</span>}
        </span>
      ),
    },
    { key: 'urgency', header: 'Estado', render: (row) => <UrgencyStamp urgency={row.urgency} /> },
    { key: 'suggested_quantity', header: 'Comprar', align: 'right', mono: true, render: (row) => buyText(row.suggested_quantity) },
    {
      key: 'coverage_days',
      header: 'Te alcanza para',
      align: 'right',
      mono: true,
      hideOnMobile: true,
      render: (row) => coverageText(row.coverage_days),
    },
    {
      key: 'daily_demand',
      header: 'Vendes al día',
      align: 'right',
      mono: true,
      hideOnMobile: true,
      render: (row) => `~${formatNumber(row.daily_demand)} u.`,
    },
    {
      key: 'detail',
      header: '',
      align: 'right',
      render: (row) => (
        <Button size="small" onClick={() => setSelected(row)} aria-label={`Ver por qué: ${row.name}`}>
          Ver por qué
        </Button>
      ),
    },
  ]

  return (
    <>
      <PageHeader
        title="Qué comprar"
        subtitle="Tus 15 productos más vendidos del último mes, lo más urgente primero, y las fechas especiales que se vienen."
      />

      {plan.loading && <Loading variant="dashboard" label="Revisando tus ventas e inventario…" />}
      {plan.error && !plan.loading && <ErrorView error={plan.error} onRetry={plan.reload} />}

      {!plan.loading && !plan.error && items.length === 0 && (
        <Empty
          title={pending.length ? 'Aún faltan ventas para recomendar' : 'Aún no tienes productos'}
          action={
            <div className="flex flex-col items-center gap-3">
              <Button component={RouterLink} to={pending.length ? '/ventas' : '/productos'} variant="contained">
                {pending.length ? 'Cargar historial de ventas' : 'Ir a Productos'}
              </Button>
              <DemoData onChange={plan.reload} />
            </div>
          }
        >
          {pending.length
            ? 'Para recomendarte compras necesitamos al menos 30 días de ventas de cada producto.'
            : 'Registra productos y carga ventas, o prueba con datos de ejemplo.'}
        </Empty>
      )}

      {!plan.loading && !plan.error && items.length > 0 && (
        <div className="flex flex-col gap-6">
          <section aria-label="Resumen" className="grid grid-cols-1 gap-4 sm:grid-cols-3">
            <StatCard label="Comprar ya" value={count('ALTO')} hint="Se acaban antes de que llegue el pedido" strong />
            <StatCard label="Comprar pronto" value={count('MEDIO')} hint="Bajo la reserva o cerca de agotarse" />
            <StatCard label="Tienes suficiente" value={count('BAJO')} hint="No hace falta comprar todavía" />
          </section>

          <Section
            title="Tu lista de compra"
            actions={
              <Button size="small" variant="outlined" startIcon={<RefreshIcon />} onClick={plan.reload}>
                Actualizar
              </Button>
            }
          >
            <DataTable bare label="Lista de compra" columns={columns} rows={items} rowKey="product_id" />
          </Section>

          {pending.length > 0 && (
            <p className="text-sm text-ink-soft">
              Sin recomendación todavía (necesitan 30 días de ventas): {pending.join(', ')}.
            </p>
          )}
        </div>
      )}

      {!plan.loading && <SeasonalView />}
    </>
  )
}

function ProductDetail({ item, onBack }) {
  const theme = useTheme()
  const data = useApi(async () => {
    const [list, history] = await Promise.all([
      forecastingApi.list({ product_id: item.product_id, limit: 1 }),
      analyticsApi.sales({ product_id: item.product_id, period: 'daily', date_from: daysAgoISO(60), date_to: todayISO() }),
    ])
    return { forecast: list.items[0], history }
  }, [item.product_id])

  return (
    <>
      <PageHeader title={item.name} subtitle="Por qué te recomendamos esta compra." />
      <div className="mb-4">
        <Button startIcon={<ArrowBackIcon />} onClick={onBack}>
          Volver a la lista
        </Button>
      </div>

      <div className="flex flex-col gap-6">
        <Recommendation item={item} />
        {data.loading && <Loading variant="chart" label="Cargando tus ventas…" />}
        {data.error && !data.loading && <ErrorView error={data.error} onRetry={data.reload} />}
        {data.data?.forecast && (
          <ForecastView
            forecast={data.data.forecast}
            history={data.data.history}
            color={theme.palette.primary.main}
            accent={theme.palette.warning.main}
          />
        )}
        <AccuracyView productId={item.product_id} />
        <CoOccurrenceView productId={item.product_id} />
      </div>
    </>
  )
}

function Recommendation({ item }) {
  const coverage = item.coverage_days == null ? null : Math.floor(item.coverage_days)
  let why
  if (item.current_stock <= 0) why = `Está agotado y vendes unas ${formatNumber(item.daily_demand)} al día.`
  else if (coverage == null) why = `No ha tenido ventas recientes: tus ${formatNumber(item.current_stock)} u. alcanzan.`
  else
    why = `Con ${formatNumber(item.current_stock)} u. y unas ${formatNumber(item.daily_demand)} ventas al día, te alcanza para ${coverage} días.`
  const supplier = `Tu proveedor tarda ${item.lead_time_days} días en traerlo y quieres guardar al menos ${formatNumber(item.min_stock)} u. de reserva.`

  return (
    <Section title="Recomendación" actions={<UrgencyStamp urgency={item.urgency} />}>
      <p className="mb-4 text-sm text-ink">
        {why} {supplier}{' '}
        <strong>
          {item.suggested_quantity > 0 ? `Compra ${formatNumber(item.suggested_quantity)} u.` : 'Por ahora no necesitas comprar.'}
        </strong>
      </p>
      <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
        <StatCard variant="inset" label="Comprar" value={buyText(item.suggested_quantity)} strong />
        <StatCard variant="inset" label="Te alcanza para" value={coverageText(item.coverage_days)} />
        <StatCard variant="inset" label="Tienes hoy" value={`${formatNumber(item.current_stock)} u.`} />
        <StatCard variant="inset" label="Reserva mínima" value={`${formatNumber(item.min_stock)} u.`} />
      </div>
    </Section>
  )
}

function ForecastView({ forecast, history, color, accent }) {
  const historyPoints = history?.series ?? []
  const forecastPoints = forecast.daily_prediction ?? []
  const historyLabels = historyPoints.map((point) => point.period)
  const forecastLabels = forecastPoints.map((point) => point.date)
  const labels = [...historyLabels, ...forecastLabels]
  const historyData = [...historyPoints.map((point) => point.units), ...forecastLabels.map(() => null)]
  const forecastData = [...historyLabels.map(() => null), ...forecastPoints.map((point) => point.value)]
  const trust = reliability(forecast.confidence)

  return (
    <Section title="Lo que vendiste y lo que esperamos vender" label="Ventas pasadas y esperadas">
      <p className="mb-4 text-sm text-ink-soft">
        {MODEL_EXPLAIN[forecast.model_type] ?? 'Usamos tu historial de ventas.'} Nos basamos en{' '}
        {formatNumber(forecast.history_days)} días de ventas.
      </p>
      <div className="mb-4 grid grid-cols-1 gap-4 sm:grid-cols-2">
        <StatCard
          variant="inset"
          label={`Esperamos vender en ${forecast.forecast_days} días`}
          value={`${formatNumber(Math.round(forecast.predicted_demand))} u.`}
        />
        <StatCard variant="inset" label="Qué tan fiable es" value={trust.label} hint={trust.hint} />
      </div>
      {labels.length > 0 && (
        <LineChart
          height={300}
          xAxis={[{ scaleType: 'band', data: labels }]}
          series={[
            { data: historyData, label: 'Lo que vendiste', color, curve: 'monotoneX' },
            { data: forecastData, label: 'Lo que esperamos', color: accent, curve: 'monotoneX' },
          ]}
          margin={{ left: 56, right: 16, top: 24, bottom: 40 }}
        />
      )}
    </Section>
  )
}

const ACCURACY_COLUMNS = [
  {
    key: 'forecast_start',
    header: 'Periodo',
    render: (row) => `${formatDate(row.forecast_start)} – ${formatDate(row.forecast_end)}`,
  },
  { key: 'predicted_total', header: 'Esperábamos', align: 'right', mono: true, render: (row) => `${formatNumber(row.predicted_total)} u.` },
  { key: 'actual_total', header: 'Vendiste', align: 'right', mono: true, render: (row) => `${formatNumber(row.actual_total)} u.` },
  {
    key: 'accuracy',
    header: 'Acierto',
    align: 'right',
    mono: true,
    hideOnMobile: true,
    render: (row) => (row.accuracy == null ? 'Sin ventas' : formatPercent(row.accuracy)),
  },
]

function AccuracyView({ productId }) {
  const { data, loading, error, reload } = useApi(() => forecastingApi.accuracy({ product_id: productId }), [productId])
  const evaluated = data?.evaluated ?? 0

  return (
    <Section title="Qué tan acertadas han sido las predicciones" label="Acierto de predicciones pasadas">
      {loading && <Loading variant="list" rows={2} label="Comparando con tus ventas…" />}
      {error && !loading && <ErrorView error={error} onRetry={reload} />}
      {data && !loading && evaluated === 0 && (
        <Empty title="Todavía no hay con qué comparar">
          Cuando pasen los días de una predicción, aquí verás cuánto esperábamos vender y cuánto vendiste de
          verdad. Vuelve cuando termine el periodo que acabas de predecir.
        </Empty>
      )}
      {data && !loading && evaluated > 0 && (
        <div className="flex flex-col gap-4">
          <p className="text-sm text-ink-soft">
            {data.accuracy == null
              ? `En esos días no hubo ventas de este producto y esperábamos ${formatNumber(data.predicted_total)} u.`
              : `En las últimas ${evaluated} predicciones esperábamos vender ${formatNumber(data.predicted_total)} u. y vendiste ${formatNumber(data.actual_total)} u. Día a día nos equivocamos en unas ${formatNumber(
                  Math.round(data.mae * 10) / 10,
                )} u.`}
          </p>
          <div className="grid grid-cols-2 gap-4 sm:grid-cols-3">
            <StatCard
              variant="inset"
              label="Acierto promedio"
              value={data.accuracy == null ? '—' : formatPercent(data.accuracy)}
              hint="100 % = acertamos exacto"
              strong
            />
            <StatCard variant="inset" label="Periodos revisados" value={evaluated} />
          </div>
          <DataTable bare label="Predicciones pasadas" columns={ACCURACY_COLUMNS} rows={data.items} rowKey="forecast_id" maxHeight={256} />
        </div>
      )}
    </Section>
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

const SEASONAL_COLUMNS = [
  { key: 'name', header: 'Producto' },
  { key: 'lift', header: 'Se vende', align: 'right', mono: true, render: (row) => `×${formatNumber(row.lift)} lo normal` },
  { key: 'extra_units', header: 'Compra de más', align: 'right', mono: true, render: (row) => `+${formatNumber(row.extra_units)} u.` },
  { key: 'order_by', header: 'Pide antes del', align: 'right', mono: true, render: (row) => formatDate(row.order_by) },
  {
    key: 'current_stock',
    header: 'Tienes hoy',
    align: 'right',
    mono: true,
    hideOnMobile: true,
    render: (row) => `${formatNumber(row.current_stock)} u.`,
  },
]

const eventTone = (days) => (days <= 14 ? 'crit' : days <= 45 ? 'warn' : 'neutral')

function SeasonalView() {
  const { data, loading, error, reload } = useApi(() => recommendationsApi.seasonal(), [])
  const events = data?.events ?? []

  return (
    <div className="mt-6 flex flex-col gap-6">
      {loading && <Loading variant="list" rows={3} label="Revisando fechas especiales…" />}
      {error && !loading && <ErrorView error={error} onRetry={reload} />}
      {data && !loading && events.length === 0 && (
        <Section title="Fechas especiales que se vienen">
          <p className="text-sm text-ink-soft">
            Cuando tengas al menos un año de ventas, aquí te avisaremos qué productos se disparan en fechas como San
            Valentín, Amor y Amistad o fin de año, y cuánto comprar de más.
          </p>
        </Section>
      )}
      {events.map((event) => {
        const top = event.items[0]
        return (
          <Section
            key={event.key}
            title={`${event.name} · ${formatDate(event.date)}`}
            label={`Productos que suben en ${event.name}`}
            actions={
              <Stamp tone={eventTone(event.days_until)}>
                {event.days_until <= 0 ? 'Es ahora' : `En ${event.days_until} días`}
              </Stamp>
            }
          >
            <p className="mb-4 text-sm text-ink-soft">
              {top.years > 1 ? `En los últimos ${top.years} años` : 'El año pasado'}, alrededor de esta fecha vendiste{' '}
              <strong className="text-ink">
                {formatNumber(top.lift)} veces más {top.name}
              </strong>{' '}
              de lo normal{event.items.length > 1 && `, y subieron ${event.items.length - 1} productos más`}. Pide lo
              extra antes del día indicado para que te llegue a tiempo.
            </p>
            <DataTable bare label={`Productos de ${event.name}`} columns={SEASONAL_COLUMNS} rows={event.items} rowKey="product_id" />
          </Section>
        )
      })}
    </div>
  )
}
