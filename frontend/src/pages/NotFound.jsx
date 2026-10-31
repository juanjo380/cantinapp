import Button from '@mui/material/Button'
import { Link as RouterLink } from 'react-router-dom'
import Logo from '../components/ui/Logo'

export default function NotFound() {
  return (
    <main className="grid min-h-svh place-items-center bg-ground px-4 text-center">
      <div className="surface flex flex-col items-center p-10">
        <Logo size="sm" />
        <p className="mt-6 text-stamp font-bold tracking-stamp uppercase text-ink-soft">Error 404</p>
        <h1 className="mt-2 text-4xl text-ink">Esta página no existe</h1>
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
