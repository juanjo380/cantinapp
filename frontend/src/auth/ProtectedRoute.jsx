import { Navigate, Outlet, useLocation } from 'react-router-dom'
import { useAuth } from './context'
import { Loading } from '../components/ui/States'

export default function ProtectedRoute() {
  const { user, initializing } = useAuth()
  const location = useLocation()

  if (initializing) return <Loading label="Verificando tu sesión…" />
  if (!user) return <Navigate to="/login" replace state={{ from: location.pathname }} />
  return <Outlet />
}
