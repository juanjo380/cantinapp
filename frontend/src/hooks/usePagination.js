import { useState } from 'react'

// Estado de paginación para DataTable; `reset` vuelve a la primera página al cambiar filtros.
export function usePagination(initialRows = 20) {
  const [page, setPage] = useState(0)
  const [rowsPerPage, setRows] = useState(initialRows)
  return {
    page,
    rowsPerPage,
    setPage,
    setRowsPerPage: (n) => {
      setRows(n)
      setPage(0)
    },
    reset: () => setPage(0),
    params: { limit: rowsPerPage, offset: page * rowsPerPage },
  }
}
