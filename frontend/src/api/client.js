const API_URL = import.meta.env.VITE_API_URL || ''
const TOKEN_KEY = 'cantinapp.token'

export function getToken() {
  return localStorage.getItem(TOKEN_KEY)
}

export function setToken(token) {
  if (token) localStorage.setItem(TOKEN_KEY, token)
  else localStorage.removeItem(TOKEN_KEY)
}

export class ApiError extends Error {
  constructor(message, status, payload) {
    super(message)
    this.name = 'ApiError'
    this.status = status
    this.payload = payload
  }
}

function messageFrom(data, status) {
  if (!data) return `Ocurrió un error (${status}).`
  const detail = data.detail
  if (typeof detail === 'string') return detail
  if (Array.isArray(detail)) {
    return detail.map((e) => e.message || e.msg || JSON.stringify(e)).join(' ')
  }
  return data.message || `Ocurrió un error (${status}).`
}

// `path` va sin el prefijo /api: se agrega aquí.
// `auth: false` en login/registro: un token viejo guardado no debe viajar ni convertir un 401 de credenciales en "sesión expirada".
export async function request(path, { method = 'GET', body, formData, signal, auth = true } = {}) {
  const headers = {}
  const token = auth ? getToken() : null
  if (token) headers.Authorization = `Bearer ${token}`
  let payload
  if (formData) {
    payload = formData
  } else if (body !== undefined) {
    headers['Content-Type'] = 'application/json'
    payload = JSON.stringify(body)
  }

  let res
  try {
    res = await fetch(`${API_URL}/api${path}`, { method, headers, body: payload, signal })
  } catch (err) {
    if (err.name === 'AbortError') throw err
    throw new ApiError('No se pudo conectar con el servidor. Revisa tu conexión e inténtalo de nuevo.', 0, null)
  }

  if (res.status === 204) return null

  const text = await res.text()
  let data = null
  if (text) {
    try {
      data = JSON.parse(text)
    } catch {
      data = text
    }
  }

  if (res.status === 401 && token) {
    // Solo cierra la sesión si el 401 es del token vigente: un 401 tardío de un token
    // viejo (p. ej. durante el cold start) no debe borrar un login recién hecho.
    if (token === getToken()) {
      setToken(null)
      window.dispatchEvent(new Event('cantinapp:unauthorized'))
    }
    throw new ApiError('Tu sesión expiró. Inicia sesión de nuevo.', 401, data)
  }
  if (!res.ok) throw new ApiError(messageFrom(data, res.status), res.status, data)
  return data
}
