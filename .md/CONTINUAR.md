# CONTINUAR — Estado del frontend CantinAPP

Documento de relevo. El backend **ya está completo y desplegado**; todo el trabajo restante es del frontend (`frontend/`).

## Estado actual

Fases 0 a 4 **implementadas** y con `npm run lint` y `npm run build` en verde.

Rutas (todas consumen la API real, sin datos quemados):

| Ruta | Pantalla | Endpoints |
|------|----------|-----------|
| `/login`, `/registro` | Acceso | `POST /api/auth/login`, `POST /api/auth/register`, `GET /api/auth/me`, `POST /api/auth/logout` |
| `/` | Dashboard | `GET /api/dashboard?trend_days` |
| `/productos` | Productos + CSV | `GET/POST/PATCH /api/products`, `POST /api/products/import` |
| `/inventario` | Inventario + movimientos | `GET /api/inventory`, `GET/POST /api/inventory/movements` |
| `/ventas` | Venta manual + import | `GET/POST /api/sales`, `POST /api/sales/import` |
| `/analisis` | Analítica | `GET /api/analytics/sales`, `GET /api/analytics/top-products` |
| `/reabastecimiento` | Pronóstico + recomendación | `POST /api/forecasting`, `GET /api/recommendations` |
| `/alertas` | Alertas | `GET /api/alerts`, `POST /api/alerts/generate`, `PATCH /api/alerts/{id}/review` |

Contrato verificado contra el OpenAPI desplegado: nombres de campos y parámetros coinciden.

## Decisiones clave

- **Mundo visual «Kraft y sello»** (ver `DESIGN.md`): riel verde, suelo kraft, sellos de goma, cifras tabulares, plano por defecto. Claro + oscuro (sistema + `data-theme`), conmutador manual en el riel.
- **Tailwind para layout, MUI para componentes**. Único CSS: `src/index.css` (`@theme` + variables claro/oscuro). `theme.js` refleja esos tokens.
- Convivencia MUI+Tailwind: `@layer theme, base, mui, components, utilities;` + `StyledEngineProvider enableCssLayer`; sin `CssBaseline` (lo cubre el preflight de Tailwind).
- ESLint: `react-hooks/set-state-in-effect` está **desactivada** en `eslint.config.js` (los hooks de carga y el arranque de sesión usan `setState` en un effect de forma intencional).
- `useApi` mantiene el fetcher en un ref actualizado dentro de un effect (no durante el render).

## Pendiente / a tener en cuenta

1. **CORS en Render**: el backend debe incluir el origen del frontend en `CORS_ORIGINS` (p. ej. `http://localhost:5173` y el dominio de despliegue del frontend). Es la única causa probable de fallo de peticiones en local.
2. **Prueba manual en navegador**: responsive (móvil ~360 px, tablet, escritorio), navegación por teclado y foco visible, contraste en modo oscuro, y aviso de cold start.
3. **HU08 incompleta en el backend**: `GET /api/dashboard` no devuelve predicción; el Dashboard enlaza a `/reabastecimiento`. Si el backend añade ese dato, incorporarlo aquí.
4. **Despliegue del frontend**: servir como SPA con fallback a `index.html`.
5. **Bundle** (opcional): `index-*.js` ≈ 366 kB (gzip 116 kB). Se puede dividir más si hiciera falta; `@mui/x-charts` ya va en un chunk aparte (`LineChart`).

## Cómo verificar

```powershell
# desde frontend/
npm run lint
npm run build
npm run dev    # http://localhost:5173 (requiere CORS del backend)
```

Revisar además el detector de Impeccable sobre `frontend/src` (sin hallazgos a la fecha).
