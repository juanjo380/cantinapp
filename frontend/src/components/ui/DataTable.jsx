import IconButton from '@mui/material/IconButton'
import Table from '@mui/material/Table'
import TableBody from '@mui/material/TableBody'
import TableCell from '@mui/material/TableCell'
import TableContainer from '@mui/material/TableContainer'
import TableHead from '@mui/material/TableHead'
import TablePagination from '@mui/material/TablePagination'
import TableRow from '@mui/material/TableRow'
import Tooltip from '@mui/material/Tooltip'
import { Empty, ErrorView, Loading } from './States'

// columns: [{ key, header, align, mono, hideOnMobile, render(row) }]
// pagination: el objeto de usePagination + `total`; si falta, la tabla no pagina.
export default function DataTable({
  columns,
  rows,
  rowKey = 'id',
  label,
  loading,
  error,
  onRetry,
  empty = <Empty title="Sin datos para mostrar" />,
  pagination,
  maxHeight,
  bare = false,
}) {
  if (loading) return <Loading label={`Cargando ${label?.toLowerCase() ?? ''}…`} />
  if (error) return <ErrorView error={error} onRetry={onRetry} />
  if (!rows?.length) return empty

  const cellClass = (col) =>
    [col.mono && 'font-mono', col.hideOnMobile && 'hidden sm:table-cell', col.className]
      .filter(Boolean)
      .join(' ') || undefined

  return (
    <div className={bare ? undefined : 'surface overflow-hidden'}>
      <TableContainer sx={maxHeight ? { maxHeight } : undefined}>
        <Table size="small" aria-label={label} stickyHeader={Boolean(maxHeight)}>
          <TableHead>
            <TableRow>
              {columns.map((col) => (
                <TableCell key={col.key} align={col.align} className={cellClass({ ...col, mono: false })}>
                  {col.header}
                </TableCell>
              ))}
            </TableRow>
          </TableHead>
          <TableBody>
            {rows.map((row, index) => (
              <TableRow key={row[rowKey] ?? index} hover>
                {columns.map((col) => (
                  <TableCell key={col.key} align={col.align} className={cellClass(col)}>
                    {col.render ? col.render(row) : (row[col.key] ?? '—')}
                  </TableCell>
                ))}
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>
      {pagination && (
        <TablePagination
          component="div"
          count={pagination.total ?? rows.length}
          page={pagination.page}
          onPageChange={(_, next) => pagination.setPage(next)}
          rowsPerPage={pagination.rowsPerPage}
          onRowsPerPageChange={(e) => pagination.setRowsPerPage(parseInt(e.target.value, 10))}
          rowsPerPageOptions={[10, 20, 50]}
          labelRowsPerPage="Filas"
          labelDisplayedRows={({ from, to, count }) => `${from}–${to} de ${count}`}
        />
      )}
    </div>
  )
}

// Acción de fila compacta: icono con tooltip y etiqueta accesible.
export function RowAction({ title, icon, onClick, color }) {
  return (
    <Tooltip title={title}>
      <IconButton size="small" aria-label={title} onClick={onClick} color={color}>
        {icon}
      </IconButton>
    </Tooltip>
  )
}
