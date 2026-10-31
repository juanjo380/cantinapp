import Inventory2OutlinedIcon from '@mui/icons-material/Inventory2Outlined'
import LayersOutlinedIcon from '@mui/icons-material/LayersOutlined'
import PaidOutlinedIcon from '@mui/icons-material/PaidOutlined'
import AutoAwesomeIcon from '@mui/icons-material/AutoAwesome'
import TrendingUpIcon from '@mui/icons-material/TrendingUp'
import Button from '@mui/material/Button'
import { useTheme } from '@mui/material/styles'
import { LineChart } from '@mui/x-charts/LineChart'
import { Link as RouterLink } from 'react-router-dom'
import { dashboardApi } from '../api/helper'
import PageHeader from '../components/ui/PageHeader'
import Section from '../components/ui/Section'
import StatCard from '../components/ui/StatCard'
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
        <Button component={RouterLink} to="/reabastecimiento" variant="contained" endIcon={<AutoAwesomeIcon />}>
          Ver recomendaciones
        </Button>
      </PageHeader>

      {loading && <Loading label="Cargando tu negocio…" />}
      {error && !loading && <ErrorView error={error} onRetry={reload} />}

      {data && !loading && !error && (
        <div className="flex flex-col gap-8">
          <section aria-label="Indicadores" className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-4">
            <StatCard label="Productos" icon={<Inventory2OutlinedIcon />} value={formatNumber(data.total_products)} />
            <StatCard label="Stock total" icon={<LayersOutlinedIcon />} value={formatNumber(data.total_stock)} hint="Unidades" />
            <StatCard label="Valor del inventario" icon={<PaidOutlinedIcon />} value={formatCOP(data.inventory_value)} />
            <StatCard
              label="Ventas del período"
              icon={<TrendingUpIcon />}
              value={formatCOP(data.current_period?.revenue ?? 0)}
              hint={`${formatNumber(data.current_period?.units_sold ?? 0)} unidades`}
            />
          </section>

          <Section title="Tendencia (últimos 30 días)" label="Tendencia de ventas">
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
          </Section>

          <Section
            title="Productos que requieren abastecimiento"
            label="Productos con bajo stock"
            actions={
              <RouterLink to="/inventario" className="sketch-link text-sm">
                Ver inventario
              </RouterLink>
            }
          >
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
          </Section>
        </div>
      )}
    </>
  )
}
