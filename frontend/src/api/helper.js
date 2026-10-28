import { request } from './client'

// Cada función corresponde 1:1 a un endpoint de memoria.md §7.
function qs(params = {}) {
  const sp = new URLSearchParams()
  for (const [key, value] of Object.entries(params)) {
    if (value === undefined || value === null || value === '') continue
    sp.set(key, value)
  }
  const s = sp.toString()
  return s ? `?${s}` : ''
}

export const authApi = {
  register: (body) => request('/auth/register', { method: 'POST', body, auth: false }),
  login: (body) => request('/auth/login', { method: 'POST', body, auth: false }),
  logout: () => request('/auth/logout', { method: 'POST' }),
  me: () => request('/auth/me'),
}

export const productsApi = {
  list: (params) => request(`/products${qs(params)}`),
  get: (id) => request(`/products/${id}`),
  create: (body) => request('/products', { method: 'POST', body }),
  update: (id, body) => request(`/products/${id}`, { method: 'PUT', body }),
  remove: (id) => request(`/products/${id}`, { method: 'DELETE' }),
}

export const inventoryApi = {
  list: (params) => request(`/inventory${qs(params)}`),
  get: (id) => request(`/inventory/${id}`),
  movements: (id, params) => request(`/inventory/${id}/movements${qs(params)}`),
  createMovement: (body) => request('/inventory/movements', { method: 'POST', body }),
}

export const salesApi = {
  list: (params) => request(`/sales${qs(params)}`),
  create: (body) => request('/sales', { method: 'POST', body }),
  importCsv: (file, affectsInventory) => {
    const form = new FormData()
    form.append('file', file)
    return request(`/sales/import${qs({ affects_inventory: affectsInventory })}`, {
      method: 'POST',
      formData: form,
    })
  },
}

export const analyticsApi = {
  sales: (params) => request(`/analytics/sales${qs(params)}`),
  topProducts: (params) => request(`/analytics/top-products${qs(params)}`),
}

export const forecastingApi = {
  create: (body) => request('/forecasting', { method: 'POST', body }),
  list: (params) => request(`/forecasting${qs(params)}`),
}

export const recommendationsApi = {
  create: (body) => request('/recommendations', { method: 'POST', body }),
  list: (params) => request(`/recommendations${qs(params)}`),
}

export const dashboardApi = {
  get: (params) => request(`/dashboard${qs(params)}`),
}

export const alertsApi = {
  list: (params) => request(`/alerts${qs(params)}`),
  generate: () => request('/alerts/generate', { method: 'POST' }),
  review: (id) => request(`/alerts/${id}/review`, { method: 'PATCH' }),
}
