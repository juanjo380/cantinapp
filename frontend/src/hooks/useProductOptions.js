import { productsApi } from '../api/helper'
import { useApi } from './useApi'

// Catálogo para selects y para resolver nombres por id.
// shortcut: trae como máximo 200 productos, paginar o usar autocompletado remoto si el catálogo crece.
export function useProductOptions({ activeOnly = true } = {}) {
  const query = useApi(() => productsApi.list({ active_only: activeOnly, limit: 200, sort: 'name' }), [activeOnly])
  return { ...query, items: query.data?.items ?? [] }
}
