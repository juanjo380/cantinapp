const cop = new Intl.NumberFormat('es-CO', {
  style: 'currency',
  currency: 'COP',
  maximumFractionDigits: 0,
})
const number = new Intl.NumberFormat('es-CO')

export const formatCOP = (value) => cop.format(Number(value) || 0)
export const formatNumber = (value) => number.format(Number(value) || 0)

export function formatDate(iso) {
  if (!iso) return '—'
  const [year, month, day] = String(iso).slice(0, 10).split('-')
  return `${day}/${month}/${year}`
}

export function formatDateTime(iso) {
  if (!iso) return '—'
  return new Date(iso).toLocaleString('es-CO', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}

export function toISODate(date) {
  const d = new Date(date)
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(
    d.getDate(),
  ).padStart(2, '0')}`
}

export function daysAgoISO(days) {
  const d = new Date()
  d.setDate(d.getDate() - days)
  return toISODate(d)
}

export const todayISO = () => toISODate(new Date())

export const formatPercent = (value) =>
  new Intl.NumberFormat('es-CO', { style: 'percent', maximumFractionDigits: 0 }).format(
    Number(value) || 0,
  )
