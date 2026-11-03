import GlobalStyles from '@mui/material/GlobalStyles'
import { StyledEngineProvider, ThemeProvider } from '@mui/material/styles'
import { lazy, Suspense, useCallback, useEffect, useMemo, useState } from 'react'
import { BrowserRouter, Route, Routes } from 'react-router-dom'
import { getToken, setToken } from './api/client'
import { authApi } from './api/helper'
import { AuthContext } from './auth/context'
import ProtectedRoute from './auth/ProtectedRoute'
import AppLayout from './components/layout/AppLayout'
import { AppShellSkeleton } from './components/ui/States'
import Login from './pages/Login'
import NotFound from './pages/NotFound'
import Register from './pages/Register'
import { getTheme } from './theme'
import { ColorModeContext, useColorMode } from './theme/color-mode'

const Dashboard = lazy(() => import('./pages/Dashboard'))
const Products = lazy(() => import('./pages/Products'))
const Inventory = lazy(() => import('./pages/Inventory'))
const Sales = lazy(() => import('./pages/Sales'))
const Analytics = lazy(() => import('./pages/Analytics'))
const Replenishment = lazy(() => import('./pages/Replenishment'))
const Alerts = lazy(() => import('./pages/Alerts'))
const Profile = lazy(() => import('./pages/Profile'))

const SESSION_KEY = 'cantinapp.session'
const LEGACY_KEYS = ['cantinapp.user', 'cantinapp.business'] // formato anterior a multi-negocio
const MODE_KEY = 'cantinapp.mode'

function ColorModeProvider({ children }) {
  const [mode, setMode] = useState(() => localStorage.getItem(MODE_KEY) || 'system')
  const [systemDark, setSystemDark] = useState(
    () => window.matchMedia('(prefers-color-scheme: dark)').matches,
  )

  useEffect(() => {
    const mq = window.matchMedia('(prefers-color-scheme: dark)')
    const handler = (event) => setSystemDark(event.matches)
    mq.addEventListener('change', handler)
    return () => mq.removeEventListener('change', handler)
  }, [])

  useEffect(() => {
    localStorage.setItem(MODE_KEY, mode)
    const root = document.documentElement
    if (mode === 'system') root.removeAttribute('data-theme')
    else root.setAttribute('data-theme', mode)
  }, [mode])

  const active = mode === 'system' ? (systemDark ? 'dark' : 'light') : mode
  const value = useMemo(() => ({ mode, active, setMode }), [mode, active])
  return <ColorModeContext.Provider value={value}>{children}</ColorModeContext.Provider>
}

// Sesión = respuesta de /auth/me: { user, business_id, business_name, role, profile_completed, businesses }.
function readSession() {
  try {
    return JSON.parse(localStorage.getItem(SESSION_KEY) || 'null')
  } catch {
    return null
  }
}

function AuthProvider({ children }) {
  const [session, setSession] = useState(readSession)
  const [initializing, setInitializing] = useState(() => Boolean(getToken()))
  // Tras iniciar sesión con varios negocios, el layout pide elegir con cuál entrar.
  const [needsPick, setNeedsPick] = useState(false)

  const apply = useCallback((next) => {
    if (next.token) setToken(next.token)
    const rest = { ...next }
    delete rest.token
    delete rest.token_type
    setSession(rest)
    localStorage.setItem(SESSION_KEY, JSON.stringify(rest))
  }, [])

  const clear = useCallback(() => {
    setToken(null)
    setSession(null)
    setNeedsPick(false)
    localStorage.removeItem(SESSION_KEY)
    LEGACY_KEYS.forEach((key) => localStorage.removeItem(key))
  }, [])

  useEffect(() => {
    if (!getToken()) {
      setInitializing(false)
      return
    }
    let alive = true
    authApi
      .me()
      .then((me) => {
        if (alive) apply(me)
      })
      // Un 401 del token vigente ya cierra la sesión vía 'cantinapp:unauthorized'. Aquí no se limpia:
      // si /me tarda (cold start) y el usuario entra mientras tanto, borraría el token nuevo; y un fallo
      // de red no significa que la sesión sea inválida.
      .catch(() => {})
      .finally(() => {
        if (alive) setInitializing(false)
      })
    return () => {
      alive = false
    }
  }, [apply])

  useEffect(() => {
    const onUnauthorized = () => clear()
    window.addEventListener('cantinapp:unauthorized', onUnauthorized)
    return () => window.removeEventListener('cantinapp:unauthorized', onUnauthorized)
  }, [clear])

  const login = useCallback(
    async (email, password) => {
      const result = await authApi.login({ email, password })
      apply(result)
      // `?.`: un backend anterior a multi-negocio no envía `businesses` (p. ej. mientras se despliega).
      setNeedsPick((result.businesses?.length ?? 0) > 1)
    },
    [apply],
  )
  const register = useCallback(async (payload) => apply(await authApi.register(payload)), [apply])
  const logout = useCallback(async () => {
    try {
      await authApi.logout()
    } catch {
      /* el JWT es sin estado: el cliente descarta el token */
    }
    clear()
  }, [clear])
  const switchBusiness = useCallback(
    async (businessId) => {
      apply(await authApi.switchBusiness(businessId))
      setNeedsPick(false)
    },
    [apply],
  )
  const createBusiness = useCallback(
    async (name) => {
      apply(await authApi.createBusiness(name))
      setNeedsPick(false)
    },
    [apply],
  )
  const refresh = useCallback(async () => apply(await authApi.me()), [apply])

  const value = useMemo(
    () => ({
      session,
      user: session?.user ?? null,
      businessName: session?.business_name ?? '',
      isAdmin: ['OWNER', 'ADMIN'].includes(session?.role),
      initializing,
      needsPick,
      setNeedsPick,
      login,
      register,
      logout,
      switchBusiness,
      createBusiness,
      refresh,
      apply,
    }),
    [session, initializing, needsPick, login, register, logout, switchBusiness, createBusiness, refresh, apply],
  )
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

function ThemedApp() {
  const { active } = useColorMode()
  const theme = useMemo(() => getTheme(active), [active])
  return (
    <StyledEngineProvider enableCssLayer>
      {/* Debe ir primero: fija el orden de capas antes de que Emotion inyecte `@layer mui`. */}
      <GlobalStyles styles="@layer theme, base, mui, components, utilities;" />
      <ThemeProvider theme={theme}>
        <BrowserRouter>
          <Suspense fallback={<AppShellSkeleton />}>
            <Routes>
              <Route path="/login" element={<Login />} />
              <Route path="/registro" element={<Register />} />
              <Route element={<ProtectedRoute />}>
                <Route element={<AppLayout />}>
                  <Route index element={<Dashboard />} />
                  <Route path="productos" element={<Products />} />
                  <Route path="inventario" element={<Inventory />} />
                  <Route path="ventas" element={<Sales />} />
                  <Route path="analisis" element={<Analytics />} />
                  <Route path="reabastecimiento" element={<Replenishment />} />
                  <Route path="alertas" element={<Alerts />} />
                  <Route path="perfil" element={<Profile />} />
                </Route>
              </Route>
              <Route path="*" element={<NotFound />} />
            </Routes>
          </Suspense>
        </BrowserRouter>
      </ThemeProvider>
    </StyledEngineProvider>
  )
}

export default function App() {
  return (
    <ColorModeProvider>
      <AuthProvider>
        <ThemedApp />
      </AuthProvider>
    </ColorModeProvider>
  )
}
