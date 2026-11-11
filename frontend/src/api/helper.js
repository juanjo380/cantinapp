import { apiUrl, request } from './client'

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
  updateMe: (body) => request('/auth/me', { method: 'PUT', body }),
  changePassword: (body) => request('/auth/password', { method: 'PUT', body }),
  forgotPassword: (email) => request('/auth/password/forgot', { method: 'POST', body: { email }, auth: false }),
  resetPassword: (body) => request('/auth/password/reset', { method: 'POST', body, auth: false }),
  switchBusiness: (businessId) => request('/auth/switch', { method: 'POST', body: { business_id: businessId } }),
  createBusiness: (name) => request('/auth/businesses', { method: 'POST', body: { name } }),
}

export const businessApi = {
  get: () => request('/business'),
  update: (body) => request('/business', { method: 'PUT', body }),
  dataSharing: () => request('/business/data-sharing'),
  setDataSharing: (enabled) => request('/business/data-sharing', { method: 'PUT', body: { enabled } }),
  locations: () => request('/business/locations'),
  createLocation: (body) => request('/business/locations', { method: 'POST', body }),
  updateLocation: (id, body) => request(`/business/locations/${id}`, { method: 'PUT', body }),
  removeLocation: (id) => request(`/business/locations/${id}`, { method: 'DELETE' }),
  members: () => request('/business/members'),
  // El rol y la sede viajan juntos: location_id null = todas las sedes.
  updateMember: (userId, role, locationId) =>
    request(`/business/members/${userId}`, { method: 'PATCH', body: { role, location_id: locationId || null } }),
  removeMember: (userId) => request(`/business/members/${userId}`, { method: 'DELETE' }),
  invitations: () => request('/business/invitations'),
  invite: (body) => request('/business/invitations', { method: 'POST', body }),
  revokeInvitation: (id) => request(`/business/invitations/${id}`, { method: 'DELETE' }),
  previewInvitation: (token) => request(`/business/invitations/preview${qs({ token })}`),
  acceptInvitation: (body) => request('/business/invitations/accept', { method: 'POST', body }),
}

export const productsApi = {
  list: (params) => request(`/products${qs(params)}`),
  get: (id) => request(`/products/${id}`),
  create: (body) => request('/products', { method: 'POST', body }),
  update: (id, body) => request(`/products/${id}`, { method: 'PUT', body }),
  remove: (id) => request(`/products/${id}`, { method: 'DELETE' }),
  importCsv: (file) => {
    const form = new FormData()
    form.append('file', file)
    return request('/products/import', { method: 'POST', formData: form })
  },
  templateUrl: apiUrl('/products/import/template'),
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
  importCsv: (file, affectsInventory, confirmReimport = false, locationId = undefined) => {
    const form = new FormData()
    form.append('file', file)
    const params = {
      affects_inventory: affectsInventory,
      confirm_reimport: confirmReimport || undefined,
      location_id: locationId || undefined,
    }
    return request(`/sales/import${qs(params)}`, {
      method: 'POST',
      formData: form,
    })
  },
  templateUrl: apiUrl('/sales/import/template'),
}

export const analyticsApi = {
  sales: (params) => request(`/analytics/sales${qs(params)}`),
  topProducts: (params) => request(`/analytics/top-products${qs(params)}`),
  classification: (params) => request(`/analytics/classification${qs(params)}`),
}

export const forecastingApi = {
  create: (body) => request('/forecasting', { method: 'POST', body }),
  list: (params) => request(`/forecasting${qs(params)}`),
  accuracy: (params) => request(`/forecasting/accuracy${qs(params)}`),
}

export const recommendationsApi = {
  create: (body) => request('/recommendations', { method: 'POST', body }),
  plan: () => request('/recommendations/plan', { method: 'POST' }),
  seasonal: () => request('/recommendations/seasonal'),
  list: (params) => request(`/recommendations${qs(params)}`),
  cooccurrence: (params) => request(`/recommendations/cooccurrence${qs(params)}`),
  recomputeCooccurrence: () => request('/recommendations/cooccurrence/recompute', { method: 'POST' }),
}

export const dashboardApi = {
  get: (params) => request(`/dashboard${qs(params)}`),
}

export const demoApi = {
  status: () => request('/demo'),
  load: () => request('/demo', { method: 'POST' }),
  remove: () => request('/demo', { method: 'DELETE' }),
}

export const alertsApi = {
  list: (params) => request(`/alerts${qs(params)}`),
  generate: () => request('/alerts/generate', { method: 'POST' }),
  review: (id) => request(`/alerts/${id}/review`, { method: 'PATCH' }),
}
