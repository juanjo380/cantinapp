import GlobalStyles from '@mui/material/GlobalStyles'
import { StyledEngineProvider, ThemeProvider } from '@mui/material/styles'
import { lazy, Suspense, useCallback, useEffect, useMemo, useState } from 'react'
import { BrowserRouter, Route, Routes } from 'react-router-dom'
import { getToken, setToken } from './api/client'
import { authApi } from './api/helper'
import { AuthContext } from './auth/context'
import ProtectedRoute from './auth/ProtectedRoute'
import AppLayout from './components/layout/AppLayout'
import { Loading } from './components/ui/States'
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

const USER_KEY = 'cantinapp.user'
const BUSINESS_KEY = 'cantinapp.business'
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

function AuthProvider({ children }) {
  const [user, setUser] = useState(() => {
    try {
      return JSON.parse(localStorage.getItem(USER_KEY) || 'null')
    } catch {
      return null
    }
  })
  const [businessName, setBusinessName] = useState(() => localStorage.getItem(BUSINESS_KEY) || '')
  const [initializing, setInitializing] = useState(() => Boolean(getToken()))

  const persist = useCallback((session) => {
    setToken(session.token)
    setUser(session.user)
    setBusinessName(session.business_name || '')
    localStorage.setItem(USER_KEY, JSON.stringify(session.user))
    localStorage.setItem(BUSINESS_KEY, session.business_name || '')
  }, [])

  const clear = useCallback(() => {
    setToken(null)
    setUser(null)
    setBusinessName('')
    localStorage.removeItem(USER_KEY)
    localStorage.removeItem(BUSINESS_KEY)
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
        if (!alive) return
        setUser(me)
        localStorage.setItem(USER_KEY, JSON.stringify(me))
      })
      .catch(() => {
        if (alive) clear()
      })
      .finally(() => {
        if (alive) setInitializing(false)
      })
    return () => {
      alive = false
    }
  }, [clear])

  useEffect(() => {
    const onUnauthorized = () => clear()
    window.addEventListener('cantinapp:unauthorized', onUnauthorized)
    return () => window.removeEventListener('cantinapp:unauthorized', onUnauthorized)
  }, [clear])

  const login = useCallback(
    async (email, password) => persist(await authApi.login({ email, password })),
    [persist],
  )
  const register = useCallback(async (payload) => persist(await authApi.register(payload)), [persist])
  const logout = useCallback(async () => {
    try {
      await authApi.logout()
    } catch {
      /* el JWT es sin estado: el cliente descarta el token */
    }
    clear()
  }, [clear])

  const value = useMemo(
    () => ({ user, businessName, initializing, login, register, logout }),
    [user, businessName, initializing, login, register, logout],
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
          <Suspense fallback={<Loading />}>
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
