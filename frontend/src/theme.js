import { alpha, createTheme } from '@mui/material/styles'

// Fuente de verdad de los tokens: src/index.css (@theme + variables CSS).
// Aquí solo se refleja lo que MUI necesita; no hay decisiones visuales nuevas.
// Si cambia un valor, cámbialo primero en index.css.

const palettes = {
  light: {
    brand: '#F97316',
    brandDeep: '#EA580C',
    brandContrast: '#1C1917',
    brandTint: '#FFEDD5',
    brandInk: '#C2410C',
    ground: '#FDFBF7',
    panel: '#FFFFFF',
    field: '#FFFDF8',
    line: '#E7E5E4',
    edge: '#1C1917',
    ink: '#1C1917',
    inkSoft: '#57534E',
    ok: '#15803D',
    warn: '#A16207',
    crit: '#DC2626',
    stamp: '#78716C',
    shadow: 'rgba(28, 25, 23, 0.15)',
  },
  dark: {
    brand: '#FB923C',
    brandDeep: '#F97316',
    brandContrast: '#1C1917',
    brandTint: '#3D2614',
    brandInk: '#FDBA74',
    ground: '#1A1612',
    panel: '#24201B',
    field: '#2B2620',
    line: '#3D362E',
    edge: '#D6CDBF',
    ink: '#F5EFE6',
    inkSoft: '#B5ACA1',
    ok: '#4ADE80',
    warn: '#FBBF24',
    crit: '#F87171',
    stamp: '#A8A29E',
    shadow: 'rgba(0, 0, 0, 0.45)',
  },
}

const CONTROL_HEIGHT = 44
const CONTROL_RADIUS = 10
const SKETCH = '255px 15px 225px 15px / 15px 225px 15px 255px'
const SKETCH_ALT = '15px 225px 15px 255px / 255px 15px 225px 15px'
const SKETCH_SM = '18px 6px 16px 6px / 6px 16px 6px 18px'
const SANS = '"Inter", system-ui, "Segoe UI", sans-serif'
const DISPLAY = '"Comic Neue", "Comic Sans MS", cursive, sans-serif'

export function getTheme(mode = 'light') {
  const c = palettes[mode] ?? palettes.light
  const isDark = mode === 'dark'
  const ring = `0 0 0 3px ${alpha(c.brand, isDark ? 0.45 : 0.3)}`
  const offsetShadow = `4px 4px 0 ${c.shadow}`
  const sketchBorder = `2px solid ${c.edge}`
  const sketchPaper = {
    borderRadius: SKETCH_SM,
    border: sketchBorder,
    backgroundImage: 'none',
    boxShadow: `6px 6px 0 ${c.shadow}`,
  }

  const overline = {
    fontFamily: SANS,
    fontSize: '0.6875rem',
    fontWeight: 700,
    letterSpacing: '0.1em',
    textTransform: 'uppercase',
  }

  return createTheme({
    palette: {
      mode,
      primary: { main: c.brand, dark: c.brandDeep, light: c.brandTint, contrastText: c.brandContrast },
      secondary: { main: c.stamp, contrastText: c.panel },
      success: { main: c.ok },
      warning: { main: c.warn },
      error: { main: c.crit },
      info: { main: c.brandInk },
      background: { default: c.ground, paper: c.panel },
      text: { primary: c.ink, secondary: c.inkSoft },
      divider: c.line,
    },
    typography: {
      fontFamily: SANS,
      h1: { fontFamily: DISPLAY, fontSize: '2.25rem', fontWeight: 700, lineHeight: 1.1 },
      h2: { fontFamily: DISPLAY, fontSize: '1.5rem', fontWeight: 700, lineHeight: 1.2 },
      h3: { fontFamily: DISPLAY, fontSize: '1.25rem', fontWeight: 700, lineHeight: 1.3 },
      body1: { fontSize: '0.9375rem', lineHeight: 1.55 },
      body2: { fontSize: '0.875rem', lineHeight: 1.5 },
      button: { fontSize: '0.9375rem', fontWeight: 700, textTransform: 'none', letterSpacing: 0 },
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
            borderRadius: SKETCH,
            paddingInline: 20,
            transition: 'all .2s ease',
            '&:focus-visible': { outline: 'none', boxShadow: ring },
          },
          sizeSmall: { minHeight: 38, paddingInline: 14, fontSize: '0.875rem' },
          sizeLarge: { minHeight: 50, paddingInline: 24, fontSize: '1rem' },
          contained: {
            border: sketchBorder,
            '&:hover': { borderRadius: SKETCH_ALT, transform: 'translateY(-2px)', boxShadow: offsetShadow },
            '&:active': { transform: 'translateY(1px)', boxShadow: 'none' },
            '&.Mui-disabled': { border: `2px solid ${c.line}`, backgroundColor: c.line, color: c.inkSoft },
          },
          containedPrimary: { '&:hover': { backgroundColor: c.brandDeep } },
          outlined: {
            border: sketchBorder,
            color: c.ink,
            '&:hover': { border: sketchBorder, borderRadius: SKETCH_ALT, backgroundColor: c.brandTint },
            '&.Mui-disabled': { border: `2px solid ${c.line}`, color: c.inkSoft },
          },
          outlinedError: {
            borderColor: c.crit,
            color: c.crit,
            '&:hover': { borderColor: c.crit, backgroundColor: alpha(c.crit, 0.08) },
          },
          text: {
            paddingInline: 12,
            borderRadius: SKETCH_SM,
            '&:hover': { backgroundColor: alpha(c.brand, isDark ? 0.14 : 0.1) },
          },
          textPrimary: { color: c.brandInk },
        },
      },
      MuiIconButton: {
        styleOverrides: {
          root: {
            borderRadius: SKETCH_SM,
            color: c.inkSoft,
            transition: 'background-color .2s ease, color .2s ease',
            '&:hover': { backgroundColor: alpha(c.brand, isDark ? 0.16 : 0.12), color: c.ink },
            '&:focus-visible': { outline: 'none', boxShadow: ring },
          },
        },
      },
      MuiOutlinedInput: {
        styleOverrides: {
          root: {
            minHeight: CONTROL_HEIGHT,
            borderRadius: SKETCH_SM,
            backgroundColor: c.field,
            transition: 'box-shadow .2s ease, background-color .2s ease',
            '& .MuiOutlinedInput-notchedOutline': { borderColor: c.edge, borderWidth: 2 },
            '&:hover .MuiOutlinedInput-notchedOutline': { borderColor: c.edge },
            '&.Mui-focused': { backgroundColor: c.brandTint, boxShadow: offsetShadow },
            '&.Mui-focused .MuiOutlinedInput-notchedOutline': { borderColor: c.edge, borderWidth: 2 },
            '&.Mui-error .MuiOutlinedInput-notchedOutline': { borderColor: c.crit },
            '&.Mui-disabled': { backgroundColor: c.ground },
            '&.Mui-disabled .MuiOutlinedInput-notchedOutline': { borderColor: c.line },
          },
          input: { padding: '12px 14px', fontWeight: 500 },
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
            fontWeight: 600,
            '&.Mui-focused': { color: c.ink },
            '&.Mui-error': { color: c.crit },
          },
        },
      },
      MuiInputAdornment: {
        styleOverrides: { root: { color: c.stamp } },
      },
      MuiSelect: {
        styleOverrides: { select: { display: 'flex', alignItems: 'center' } },
      },
      MuiMenuItem: {
        styleOverrides: {
          root: {
            fontSize: '0.875rem',
            fontWeight: 500,
            borderRadius: SKETCH_SM,
            margin: '2px 6px',
            '&.Mui-selected, &.Mui-selected:hover': { backgroundColor: c.brandTint },
          },
        },
      },
      MuiCheckbox: {
        defaultProps: { color: 'primary' },
        styleOverrides: {
          root: { padding: 8, borderRadius: 8, color: c.inkSoft, '&.Mui-checked': { color: c.brand } },
        },
      },
      MuiSwitch: {
        styleOverrides: {
          switchBase: { color: c.line, '&.Mui-checked': { color: c.brand } },
          track: { backgroundColor: c.inkSoft, opacity: 0.35 },
        },
      },
      MuiFormControlLabel: {
        styleOverrides: { label: { fontSize: '0.875rem', fontWeight: 500, color: c.ink } },
      },
      MuiTableCell: {
        styleOverrides: {
          root: {
            borderBottom: `2px dashed ${c.line}`,
            padding: '14px 16px',
            fontSize: '0.875rem',
            color: c.ink,
          },
          head: {
            ...overline,
            color: c.stamp,
            backgroundColor: c.ground,
            borderBottom: sketchBorder,
            paddingTop: 12,
            paddingBottom: 12,
            whiteSpace: 'nowrap',
          },
        },
      },
      MuiTableRow: {
        styleOverrides: {
          root: {
            '&:last-child td': { borderBottom: 0 },
            '&.MuiTableRow-hover:hover': { backgroundColor: alpha(c.brand, isDark ? 0.1 : 0.07) },
          },
        },
      },
      MuiTablePagination: {
        styleOverrides: {
          root: { borderTop: `2px dashed ${c.line}`, color: c.inkSoft },
          selectIcon: { color: c.inkSoft },
        },
      },
      MuiDialog: {
        styleOverrides: { paper: sketchPaper },
      },
      MuiDialogTitle: {
        styleOverrides: {
          root: { fontFamily: DISPLAY, fontSize: '1.5rem', fontWeight: 700, padding: '20px 24px 8px' },
        },
      },
      MuiDialogActions: {
        styleOverrides: { root: { padding: '16px 24px 20px', gap: 8 } },
      },
      MuiMenu: {
        styleOverrides: { paper: { ...sketchPaper, padding: 4 } },
      },
      MuiPopover: {
        styleOverrides: { paper: sketchPaper },
      },
      MuiAlert: {
        styleOverrides: {
          root: { borderRadius: SKETCH_SM, border: '2px solid currentColor', fontWeight: 500 },
          message: { color: c.ink },
        },
      },
      MuiChip: {
        styleOverrides: { root: { borderRadius: SKETCH_SM, fontWeight: 600, border: sketchBorder } },
      },
      MuiToggleButtonGroup: {
        styleOverrides: {
          root: { borderRadius: SKETCH_SM, border: sketchBorder, backgroundColor: c.panel, overflow: 'hidden' },
          grouped: { borderColor: c.edge, borderLeft: `2px dashed ${c.line}`, borderRadius: 0 },
        },
      },
      MuiToggleButton: {
        styleOverrides: {
          root: {
            minHeight: 40,
            paddingInline: 16,
            border: 'none',
            textTransform: 'none',
            fontWeight: 700,
            fontSize: '0.875rem',
            color: c.inkSoft,
            '&.Mui-selected, &.Mui-selected:hover': { backgroundColor: c.brandTint, color: c.brandInk },
          },
        },
      },
      MuiTabs: {
        styleOverrides: {
          root: { minHeight: 44 },
          indicator: { backgroundColor: c.brand, height: 3, borderRadius: 3 },
        },
      },
      MuiTab: {
        styleOverrides: {
          root: {
            textTransform: 'none',
            fontWeight: 700,
            fontSize: '0.9375rem',
            minHeight: 44,
            color: c.inkSoft,
            '&.Mui-selected': { color: c.ink },
          },
        },
      },
      MuiTooltip: {
        styleOverrides: {
          tooltip: { backgroundColor: c.ink, color: c.ground, fontWeight: 600, borderRadius: SKETCH_SM },
        },
      },
      MuiSkeleton: {
        styleOverrides: {
          root: { borderRadius: SKETCH_SM, backgroundColor: alpha(c.ink, isDark ? 0.08 : 0.06) },
        },
      },
      MuiDivider: {
        styleOverrides: { root: { borderColor: c.line } },
      },
      MuiDrawer: {
        styleOverrides: { paper: { backgroundColor: c.ground, borderRight: sketchBorder } },
      },
    },
  })
}
