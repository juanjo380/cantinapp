import Button from '@mui/material/Button'
import { Link as RouterLink } from 'react-router-dom'

export default function NotFound() {
  return (
    <main className="grid min-h-svh place-items-center bg-ground px-4 text-center">
      <div>
        <p className="font-mono text-stamp tracking-stamp uppercase text-ink-soft">Error 404</p>
        <h1 className="mt-2 text-3xl font-black text-ink">Esta página no existe</h1>
        <p className="mt-2 text-sm text-ink-soft">
          Puede que el enlace esté mal escrito o que la página se haya movido.
        </p>
        <Button component={RouterLink} to="/" variant="contained" className="mt-6">
          Volver al dashboard
        </Button>
      </div>
    </main>
  )
}
