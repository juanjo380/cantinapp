# CantinAPP — Frontend

Interfaz web de CantinAPP (React + Vite + React Router + Material UI + Tailwind CSS v4).
Consume el backend desplegado en `https://cantinapp.onrender.com`.

## Puesta en marcha

```powershell
npm install
npm run dev      # http://localhost:5173
npm run lint
npm run build
```

La URL del backend sale de `VITE_API_URL` (ver `.env` / `.env.example`); nunca se codifica a mano.

## Estructura

- `src/api/client.js` — `fetch` con `Authorization: Bearer`; en `401` limpia la sesión y emite `cantinapp:unauthorized`.
- `src/api/helper.js` — una función por recurso de la API (productos, inventario, ventas, analítica, pronóstico, recomendaciones, dashboard, alertas).
- `src/App.jsx` — providers (tema claro/oscuro y sesión), router y rutas con carga diferida.
- `src/components/` — `layout/AppLayout.jsx` (riel de navegación, tema, logout) y `ui/` (estados, sellos, encabezado).
- `src/pages/` — una pantalla por ruta: Dashboard, Productos, Inventario, Ventas, Análisis, Reabastecimiento, Alertas, Login, Registro.
- `src/theme.js` — tema MUI que refleja los tokens de `src/index.css`.
- `src/index.css` — **única hoja de estilos**; define los tokens del mundo «Kraft y sello» (ver `../DESIGN.md`).

## Convenciones

- Estilos: Tailwind primero para layout y responsive; MUI solo para componentes complejos. No hay CSS por componente.
- Fechas y moneda con `Intl` (COP sin decimales, fechas DD/MM/YYYY en la interfaz, ISO `YYYY-MM-DD` hacia la API).
- Toda vista cubre estados de carga, vacío y error. El primer arranque del backend gratuito puede tardar 30–60 s («El servidor está despertando…»).
- El `business_id` nunca viaja desde el cliente: lo deduce el backend del token.

## Notas de despliegue

- Servir como SPA con fallback a `index.html` para las rutas del router.
- El backend debe permitir el origen del frontend en `CORS_ORIGINS`.
