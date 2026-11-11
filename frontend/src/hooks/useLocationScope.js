import { businessApi } from '../api/helper'
import { useAuth } from '../auth/context'
import { useApi } from './useApi'

// Sedes del negocio y la sede asignada al usuario (null = ve todas; el dueño siempre ve todas).
export function useLocationScope() {
  const { session } = useAuth()
  const own = session?.businesses?.find((b) => b.business_id === session.business_id)?.location_id ?? null
  const { data } = useApi(() => businessApi.locations(), [])
  const locations = data ?? []
  return { locations, own, main: locations.find((l) => l.is_main)?.id ?? '' }
}
