import { createContext, useContext } from 'react'

export const ColorModeContext = createContext(null)

export function useColorMode() {
  const ctx = useContext(ColorModeContext)
  if (!ctx) throw new Error('useColorMode debe usarse dentro de ColorModeProvider')
  return ctx
}
