import { useCallback, useEffect, useRef, useState } from 'react'

// Carga asíncrona con estados (loading/error/data) y recarga manual.
export function useApi(fetcher, deps = []) {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [reloadKey, setReloadKey] = useState(0)
  const fetcherRef = useRef(fetcher)

  // Mantiene el fetcher más reciente sin re-disparar el efecto.
  useEffect(() => {
    fetcherRef.current = fetcher
  })

  useEffect(() => {
    let alive = true
    setLoading(true)
    setError(null)
    Promise.resolve()
      .then(() => fetcherRef.current())
      .then((result) => {
        if (alive) setData(result)
      })
      .catch((err) => {
        if (alive) setError(err)
      })
      .finally(() => {
        if (alive) setLoading(false)
      })
    return () => {
      alive = false
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [...deps, reloadKey])

  const reload = useCallback(() => setReloadKey((k) => k + 1), [])
  return { data, loading, error, reload, setData }
}
