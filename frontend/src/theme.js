import { alpha, createTheme } from '@mui/material/styles'

// Fuente de verdad de los tokens: src/index.css (@theme + variables CSS).
// Aquí solo se refleja lo que MUI necesita; no hay decisiones visuales nuevas.
// Si cambia un valor, cámbialo primero en index.css.

const palettes = {
  light: {
    brand: '#1F5C3D',
    brandDeep: '#164430',
    brandContrast: '#FBF7EC',
    ground: '#F4EEE1',
    panel: '#FFFDF8',
    line: '#E6DCC8',
    ink: '#201A11',
    inkSoft: '#6A5C46',
    ok: '#1F7A4A',
    warn: '#946118',
    crit: '#B23A17',
    stamp: '#8A5A2B',
  },
  dark: {
    brand: '#62B98A',
    brandDeep: '#489A6C',
    brandContrast: '#14110B',
    ground: '#15120B',
    panel: '#201B13',
    line: '#37301F',
    ink: '#F2EADB',
    inkSoft: '#B4A684',
    ok: '#74C79C',
    warn: '#E7B44C',
    crit: '#F0795A',
    stamp: '#C79A6A',
  },
}

const CONTROL_HEIGHT = 44
const CONTROL_RADIUS = 10
const SURFACE_RADIUS = 14
const MONO = '"Chivo Mono", ui-monospace, "Cascadia Mono", monospace'

export function getTheme(mode = 'light') {
  const c = palettes[mode] ?? palettes.light
  const isDark = mode === 'dark'
  const ring = `0 0 0 3px ${alpha(c.brand, isDark ? 0.4 : 0.22)}`
  const ringError = `0 0 0 3px ${alpha(c.crit, isDark ? 0.4 : 0.2)}`
  const surfaceShadow = isDark
    ? '0 20px 44px rgba(0, 0, 0, 0.55)'
    : '0 20px 44px rgba(45, 33, 14, 0.14)'

  const overline = {
    fontFamily: MONO,
    fontSize: '0.6875rem',
    fontWeight: 600,
    letterSpacing: '0.08em',
    textTransform: 'uppercase',
  }

  return createTheme({
    palette: {
      mode,
      primary: { main: c.brand, dark: c.brandDeep, contrastText: c.brandContrast },
      secondary: { main: c.stamp, contrastText: c.brandContrast },
      success: { main: c.ok },
      warning: { main: c.warn },
      error: { main: c.crit },
      info: { main: c.brand },
      background: { default: c.ground, paper: c.panel },
      text: { primary: c.ink, secondary: c.inkSoft },
      divider: c.line,
    },
    typography: {
      fontFamily: '"Chivo", system-ui, "Segoe UI", sans-serif',
      h1: { fontSize: '1.75rem', fontWeight: 700, lineHeight: 1.15, letterSpacing: '-0.02em' },
      h2: { fontSize: '1.375rem', fontWeight: 600, lineHeight: 1.2, letterSpacing: '-0.01em' },
      h3: { fontSize: '1.0625rem', fontWeight: 600, lineHeight: 1.3, letterSpacing: '-0.005em' },
      body1: { fontSize: '0.9375rem', lineHeight: 1.55 },
      body2: { fontSize: '0.875rem', lineHeight: 1.5 },
      button: { fontSize: '0.875rem', fontWeight: 600, textTransform: 'none', letterSpacing: 0 },
      caption: { fontSize: '0.75rem' },
      overline,
    },
    shape: { borderRadius: CONTROL_RADIUS },
    components: {
      MuiPaper: {
        defaultProps: { elevation: 0 },
        styleOverrides: { root: { backgroundImage: 'none' } },
      },
      MuiButton: {
        defaultProps: { disableElevation: true },
        styleOverrides: {
          root: {
            minHeight: CONTROL_HEIGHT,
            borderRadius: CONTROL_RADIUS,
            paddingInline: 18,
            fontWeight: 600,
            transition: 'background-color .15s ease, border-color .15s ease, box-shadow .15s ease',
            '&:focus-visible': { outline: 'none', boxShadow: ring },
          },
          sizeSmall: { minHeight: 40, paddingInline: 14 },
          sizeLarge: { minHeight: 48, paddingInline: 22, fontSize: '0.9375rem' },
          containedPrimary: {
            '&:hover': { backgroundColor: c.brandDeep },
            '&.Mui-disabled': { backgroundColor: c.line, color: c.inkSoft },
          },
          outlined: {
            borderColor: c.line,
            color: c.ink,
            '&:hover': { borderColor: c.brand, backgroundColor: alpha(c.brand, 0.07) },
            '&.Mui-disabled': { borderColor: c.line, color: c.inkSoft },
          },
          text: { paddingInline: 12, '&:hover': { backgroundColor: alpha(c.brand, 0.09) } },
          textPrimary: { color: c.brand },
        },
      },
      MuiIconButton: {
        styleOverrides: {
          root: {
            borderRadius: CONTROL_RADIUS,
            color: c.inkSoft,
            transition: 'background-color .15s ease, color .15s ease',
            '&:hover': { backgroundColor: alpha(c.ink, isDark ? 0.12 : 0.06), color: c.ink },
            '&:focus-visible': { outline: 'none', boxShadow: ring },
          },
        },
      },
      MuiOutlinedInput: {
        styleOverrides: {
          root: {
            minHeight: CONTROL_HEIGHT,
            borderRadius: CONTROL_RADIUS,
            backgroundColor: c.panel,
            transition: 'box-shadow .15s ease',
            '& .MuiOutlinedInput-notchedOutline': { borderColor: c.line, borderWidth: 1 },
            '&:hover .MuiOutlinedInput-notchedOutline': { borderColor: c.inkSoft },
            '&.Mui-focused .MuiOutlinedInput-notchedOutline': { borderColor: c.brand, borderWidth: 1 },
            '&.Mui-focused': { boxShadow: ring },
            '&.Mui-error .MuiOutlinedInput-notchedOutline': { borderColor: c.crit },
            '&.Mui-error.Mui-focused': { boxShadow: ringError },
            '&.Mui-disabled': { backgroundColor: c.ground },
          },
          input: { padding: '12px 14px' },
          inputSizeSmall: { padding: '10px 12px' },
        },
      },
      MuiInputBase: {
        styleOverrides: { root: { fontSize: '0.9375rem' } },
      },
      MuiInputLabel: {
        styleOverrides: {
          root: {
            color: c.inkSoft,
            '&.Mui-focused': { color: c.brand },
            '&.Mui-error': { color: c.crit },
          },
        },
      },
      MuiSelect: {
        styleOverrides: { select: { display: 'flex', alignItems: 'center' } },
      },
      MuiMenuItem: {
        styleOverrides: { root: { fontSize: '0.875rem', borderRadius: 8, margin: '2px 6px' } },
      },
      MuiCheckbox: {
        defaultProps: { color: 'primary' },
        styleOverrides: {
          root: {
            padding: 8,
            borderRadius: 8,
            color: c.inkSoft,
            '&.Mui-checked': { color: c.brand },
          },
        },
      },
      MuiSwitch: {
        styleOverrides: {
          switchBase: { color: c.line, '&.Mui-checked': { color: c.brand } },
          track: { backgroundColor: c.inkSoft, opacity: 0.35 },
        },
      },
      MuiFormControlLabel: {
        styleOverrides: { label: { fontSize: '0.875rem', color: c.ink } },
      },
      MuiTableCell: {
        styleOverrides: {
          root: {
            borderBottom: `1px solid ${c.line}`,
            padding: '14px 16px',
            fontSize: '0.875rem',
            color: c.ink,
          },
          head: {
            ...overline,
            color: c.inkSoft,
            backgroundColor: c.ground,
            borderBottom: `1px solid ${c.line}`,
            paddingTop: 12,
            paddingBottom: 12,
            whiteSpace: 'nowrap',
          },
        },
      },
      MuiTableRow: {
        styleOverrides: {
          root: { '&.MuiTableRow-hover:hover': { backgroundColor: alpha(c.brand, isDark ? 0.08 : 0.05) } },
        },
      },
      MuiTablePagination: {
        styleOverrides: {
          root: { borderTop: `1px solid ${c.line}`, color: c.inkSoft },
          selectIcon: { color: c.inkSoft },
        },
      },
      MuiDialog: {
        styleOverrides: {
          paper: {
            borderRadius: SURFACE_RADIUS,
            border: `1px solid ${c.line}`,
            backgroundImage: 'none',
            boxShadow: surfaceShadow,
          },
        },
      },
      MuiDialogTitle: {
        styleOverrides: { root: { fontSize: '1.125rem', fontWeight: 600, padding: '20px 24px 8px' } },
      },
      MuiDialogActions: {
        styleOverrides: { root: { padding: '16px 24px 20px', gap: 8 } },
      },
      MuiMenu: {
        styleOverrides: {
          paper: {
            borderRadius: 12,
            border: `1px solid ${c.line}`,
            backgroundImage: 'none',
            padding: 4,
            boxShadow: surfaceShadow,
          },
        },
      },
      MuiPopover: {
        styleOverrides: {
          paper: {
            borderRadius: 12,
            border: `1px solid ${c.line}`,
            backgroundImage: 'none',
            boxShadow: surfaceShadow,
          },
        },
      },
      MuiAlert: {
        styleOverrides: { root: { borderRadius: CONTROL_RADIUS, border: `1px solid ${c.line}` } },
      },
      MuiChip: {
        styleOverrides: { root: { borderRadius: 999, fontWeight: 500 } },
      },
      MuiToggleButtonGroup: {
        styleOverrides: {
          root: { borderRadius: CONTROL_RADIUS, border: `1px solid ${c.line}`, backgroundColor: c.panel },
          grouped: { borderColor: c.line, borderLeft: `1px solid ${c.line}` },
        },
      },
      MuiToggleButton: {
        styleOverrides: {
          root: {
            minHeight: 40,
            paddingInline: 16,
            border: 'none',
            textTransform: 'none',
            fontWeight: 600,
            fontSize: '0.875rem',
            color: c.inkSoft,
            '&.Mui-selected': {
              backgroundColor: alpha(c.brand, isDark ? 0.24 : 0.12),
              color: c.brand,
              '&:hover': { backgroundColor: alpha(c.brand, isDark ? 0.3 : 0.16) },
            },
          },
        },
      },
      MuiTabs: {
        styleOverrides: { indicator: { backgroundColor: c.brand, height: 2 }, root: { minHeight: 44 } },
      },
      MuiTab: {
        styleOverrides: {
          root: {
            textTransform: 'none',
            fontWeight: 600,
            fontSize: '0.9rem',
            minHeight: 44,
            color: c.inkSoft,
            '&.Mui-selected': { color: c.brand },
          },
        },
      },
      MuiSkeleton: {
        styleOverrides: {
          root: { borderRadius: 8, backgroundColor: alpha(c.ink, isDark ? 0.08 : 0.06) },
        },
      },
      MuiDivider: {
        styleOverrides: { root: { borderColor: c.line } },
      },
    },
  })
}
