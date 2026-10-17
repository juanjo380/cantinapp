import Button from '@mui/material/Button'
import { useTheme } from '@mui/material/styles'
import { LineChart } from '@mui/x-charts/LineChart'
import { Link as RouterLink } from 'react-router-dom'
import { dashboardApi } from '../api/helper'
import PageHeader from '../components/ui/PageHeader'
import { StatusStamp } from '../components/ui/Stamp'
import { Empty, ErrorView, Loading } from '../components/ui/States'
import { useApi } from '../hooks/useApi'
import { formatCOP, formatDate, formatNumber } from '../utils/format'

export default function Dashboard() {
  const theme = useTheme()
  const { data, loading, error, reload } = useApi(() => dashboardApi.get({ trend_days: 30 }), [])

  return (
    <>
      <PageHeader title="Dashboard" subtitle="El estado de tu negocio y tus ventas del período.">
        <Button component={RouterLink} to="/reabastecimiento" variant="outlined">
          Ver recomendaciones
        </Button>
      </PageHeader>

      {loading && <Loading label="Cargando tu negocio…" />}
      {error && !loading && <ErrorView error={error} onRetry={reload} />}

      {data && !loading && !error && (
        <div className="flex flex-col gap-6">
          <section aria-label="Indicadores" className="grid grid-cols-2 gap-4 lg:grid-cols-4">
            <Kpi label="Productos" value={formatNumber(data.total_products)} />
            <Kpi label="Stock total" value={formatNumber(data.total_stock)} hint="Unidades" />
            <Kpi label="Valor del inventario" value={formatCOP(data.inventory_value)} />
            <Kpi
              label="Ventas del período"
              value={formatCOP(data.current_period?.revenue ?? 0)}
              hint={`${formatNumber(data.current_period?.units_sold ?? 0)} unidades`}
            />
          </section>

          <section aria-label="Tendencia de ventas" className="surface p-5">
            <h2 className="mb-3 text-base font-semibold text-ink">Tendencia (últimos 30 días)</h2>
            {data.trend?.length ? (
              <LineChart
                height={300}
                xAxis={[{ scaleType: 'band', data: data.trend.map((p) => p.date), valueFormatter: formatDate }]}
                series={[
                  {
                    data: data.trend.map((p) => p.units),
                    label: 'Unidades vendidas',
                    color: theme.palette.primary.main,
                    area: true,
                    curve: 'monotoneX',
                  },
                ]}
                margin={{ left: 48, right: 16, top: 24, bottom: 40 }}
              />
            ) : (
              <p className="py-10 text-center text-sm text-ink-soft">Sin ventas registradas todavía.</p>
            )}
          </section>

          <section aria-label="Productos con bajo stock" className="surface p-5">
            <div className="mb-3 flex items-center justify-between">
              <h2 className="text-base font-semibold text-ink">Productos que requieren abastecimiento</h2>
              <Button size="small" component={RouterLink} to="/inventario">
                Ver inventario
              </Button>
            </div>
            {data.low_stock_products?.length ? (
              <ul className="flex flex-col divide-y divide-line">
                {data.low_stock_products.map((product) => (
                  <li key={product.product_id} className="flex flex-wrap items-center gap-3 py-2">
                    <span className="min-w-0 flex-1 truncate text-sm font-medium text-ink">
                      {product.name}
                    </span>
                    <span className="font-mono text-sm text-ink-soft">
                      {product.stock_quantity} / mín. {product.min_stock}
                    </span>
                    <StatusStamp status={product.status} />
                  </li>
                ))}
              </ul>
            ) : (
              <Empty title="Todo con stock suficiente">
                Ningún producto está por debajo de su stock mínimo.
              </Empty>
            )}
          </section>
        </div>
      )}
    </>
  )
}

function Kpi({ label, value, hint }) {
  return (
    <div className="surface p-5">
      <p className="font-mono text-stamp tracking-stamp uppercase text-ink-soft">{label}</p>
      <p className="mt-1 text-2xl font-bold text-ink">{value}</p>
      {hint && <p className="text-xs text-ink-soft">{hint}</p>}
    </div>
  )
}
