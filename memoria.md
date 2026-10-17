# Memoria técnica — CantinAPP (backend)

Documento de contexto acumulado del proyecto. Nivel técnico general, con el
detalle necesario para construir el frontend sobre esta API.

Última actualización: backend MVP v0.1 completo (9 módulos) y **desplegado en
Render** (ver sección 9).

---

## 1. Qué es el proyecto

SaaS para pymes que gestiona inventario y predice demanda a partir de ventas
históricas. Un **negocio (tenant)** tiene usuarios; cada usuario solo ve los
datos de su negocio. Alcance v0.1 (doc `MinimoReq.md`): login, productos,
ventas (manual + CSV), inventario, análisis, predicción, recomendación
(MUST) + dashboard y alertas (SHOULD).

- **Este repositorio es backend-only por ahora.** El frontend React se
  construirá sobre esta API (puede vivir en el mismo repo, en `frontend/`).
- Fuente de verdad del esquema: `db/schema.sql`.

---

## 2. Tecnologías

| Capa | Tecnología |
|---|---|
| Lenguaje | Python 3.12 en local; **3.11.9 en Render** (`PYTHON_VERSION`) |
| API | FastAPI (async) + Uvicorn |
| Validación / DTO | Pydantic v2 + pydantic-settings |
| ORM / acceso | SQLAlchemy 2.0 async (`async_sessionmaker`) |
| Driver BD | asyncpg |
| Base de datos | PostgreSQL 15+ en **Supabase** |
| Hosting backend | **Render** (Web Service, plan gratuito) |
| Archivos CSV | `python-multipart` (upload) + módulo `csv` estándar |
| Auth | JWT HS256 + PBKDF2-SHA256, **solo librería estándar** (sin PyJWT) |
| Modelos predictivos | Python puro (sin numpy) |
| Tests | pytest (lógica pura, sin BD) |

Dependencias: `backend/requirements.txt` (runtime) y
`backend/requirements-dev.txt` (pytest).

**Nota de entorno:** crear el venv **fuera de OneDrive** (OneDrive bloquea
archivos y rompe `pip`). El directorio `backend/venv` que existe está roto
(apunta a otra máquina). El `venv/`, `node_modules/` y `__pycache__/` no deben
estar en el repo (ver `.gitignore`, sección 9).

---

## 3. Conexión a la base de datos

Configurada en `backend/app/core/config.py` (variables de entorno / `.env`).

| Variable | Descripción |
|---|---|
| `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, `DB_PASSWORD` | Datos de Supabase |
| `DB_SSL` | `true` en Supabase (conexión cifrada) |
| `DB_USE_TRANSACTION_POOLER` | `true` si se usa el pooler pgbouncer en modo transacción (puerto 6543): desactiva prepared statements y usa `NullPool` |
| `DB_POOL_SIZE`, `DB_MAX_OVERFLOW`, `DB_ECHO` | Pool / logging |
| `JWT_SECRET` | Clave de firma JWT (`dev-secret-change-me` por defecto, **cambiar en prod**) |
| `JWT_EXPIRE_MINUTES` | Expiración del token (720 por defecto) |
| `CORS_ORIGINS` | Orígenes permitidos (lista JSON; por defecto `["*"]`) |

- El motor async vive en `backend/app/shared/infrastructure/database.py`
  (`create_async_engine` + `async_sessionmaker`, `pool_pre_ping`).
- **Una sesión por request** (`get_db`), **sin commit automático**: la capa de
  aplicación hace `await session.commit()` explícito vía UnitOfWork.
- Al arrancar, `main.py` ejecuta `SELECT 1` (**fail-fast** si la BD no responde)
  y libera el motor al apagar.
- Comprobación manual: `python -m scripts.check_db` (desde `backend/`).
- **En producción (Render)** se usa el **pooler de Supabase en modo sesión**
  (host `aws-0-us-east-1.pooler.supabase.com`, puerto `5432`), con
  `DB_USE_TRANSACTION_POOLER=false`. Ver sección 9.

---

## 4. Base de datos (esquema)

Ejecutar `db/schema.sql` en el SQL Editor de Supabase **antes** de levantar la API.

**Tablas:** `businesses`, `users`, `categories`, `suppliers`, `products`,
`sales_imports`, `sales`, `inventory_movements`, `forecasts`,
`recommendations`, `alerts`.

**Vistas:** `v_inventory` (estado NORMAL/BAJO/AGOTADO calculado),
`v_daily_sales` (ventas agregadas por día).

**Decisiones clave del esquema:**
1. **Multitenancy:** toda tabla de negocio lleva `business_id` y las FK son
   compuestas `(business_id, id)`: un producto nunca puede apuntar a datos de
   otro negocio.
2. **Stock como caché:** `products.stock_quantity` solo cambia por
   `inventory_movements` (libro de movimientos). Las ventas generan un
   movimiento vía trigger; las compras/ajustes también.
3. **Borrado lógico:** productos con `is_active` (conserva historial).
4. **Ventas históricas (CSV)** pueden cargarse con `affects_inventory = false`
   para no descontar stock actual.
5. **Estado de inventario** se calcula en la vista, nunca se almacena.
6. **Triggers:** aplicar movimiento al stock (atómico, con bloqueo de fila),
   stock inicial, descuento por venta, reversión al borrar venta, `updated_at`.
7. **RLS activado sin políticas** + permisos revocados a `anon`/`authenticated`:
   la API REST de Supabase no puede leer/escribir; solo el backend (rol postgres).

---

## 5. Arquitectura y patrones

**Monolito modular** (ADR-001) con **Clean / Hexagonal** + **CQRS**. Cada
bounded context es un módulo con 4 capas:

```
backend/app/modules/<modulo>/
  domain/          entities, repository (puerto), policy/models puros
  application/     commands, queries, handlers, facade (servicios de aplicación)
  infrastructure/  models (ORM), repository (adaptador SQLAlchemy)
  api/             schemas (Pydantic), router (FastAPI)
backend/app/shared/   piezas reutilizables (base, UoW, deps, errores)
backend/app/core/     config, seguridad, excepciones
```

**Patrones aplicados:**
- **Hexagonal / Ports & Adapters:** el dominio define puertos
  (`domain/repository.py`, `Protocol`); infraestructura los implementa
  (`infrastructure/repository.py`).
- **CQRS:** comandos (escritura) y consultas (lectura) separados
  (`application/commands.py`, `queries.py`).
- **Repository:** acceso a datos encapsulado por módulo.
- **Unit of Work:** `SqlAlchemyUnitOfWork` agrupa la transacción por request.
- **Facade / Application Service:** compone repositorios + handlers y hace commit.
- **Dependency Injection:** dependencias de FastAPI (`get_db`, `get_uow`,
  `get_current_user`).
- **DTO:** entidades de dominio (dataclasses) vs. esquemas HTTP (Pydantic).

**Reglas de dependencia** (doc 1): predicción llama a análisis; recomendación
llama a predicción e inventario; alertas llama a inventario; ventas llama a
productos e inventario; dashboard puede llamar a todos. Sin ciclos ni saltos de capa.

**Errores → HTTP** (`shared/api/error_handlers.py`): excepción `AppError` con
`status_code` (401/403/404/409/422) y mapeo de `IntegrityError` de Postgres
(unique→409, check→422, FK→404). 500 por defecto.

---

## 6. Autenticación y multitenancy

- **RF-01/02:** registro crea negocio + usuario ADMIN; login devuelve JWT.
- **JWT** (`core/security.py`): HS256, claims `sub` (id usuario), `bid` (id
  negocio), `iat`, `exp`. Firma HMAC-SHA256 con `JWT_SECRET`.
- **Hash de contraseña:** PBKDF2-SHA256, 260k iteraciones, sal aleatoria.
- **Multitenancy (RNF-01):** `get_current_user` valida el token, carga el
  usuario y expone `business_id`. **Todos** los endpoints de negocio dependen de
  `get_current_user` y filtran por ese `business_id`. Nunca se acepta
  `business_id` desde el cliente.
- Errores: 401 si falta/expira/está mal el token; 404 en recursos de otro negocio
  (no se revela su existencia).

**Header obligatorio en endpoints protegidos:**
```
Authorization: Bearer <token>
```

---

## 7. Endpoints

Base local: `http://127.0.0.1:8000`. Prefijo `/api`. Swagger: `/docs`.
**Base en producción: `https://cantinapp.onrender.com`** (Swagger en
`https://cantinapp.onrender.com/docs`, esquema en `/openapi.json`).

Leyenda: 🔓 público · 🔒 requiere `Authorization: Bearer`.

### Salud

| Método | Ruta | Auth | Descripción |
|---|---|---|---|
| GET | `/health` | 🔓 | Ping de la API (lo usa Render como health check) |
| GET | `/health/db` | 🔓 | Estado de conexión a BD (503 si falla) |

### Autenticación — `/api/auth`

| Método | Ruta | Auth | Cuerpo / parámetros | Respuesta |
|---|---|---|---|---|
| POST | `/register` | 🔓 | `{ business_name, email, password (min 8), full_name? }` | 201 AuthResponse |
| POST | `/login` | 🔓 | `{ email, password }` | AuthResponse |
| POST | `/logout` | 🔒 | — | 204 (JWT sin estado: el cliente descarta el token) |
| GET | `/me` | 🔒 | — | UserOut |

- **AuthResponse:** `{ token, token_type:"bearer", user{ id, business_id, email, full_name }, business_id, business_name }`
- **UserOut:** `{ id, business_id, email, full_name }`
- Email único global (sin distinguir mayúsculas). Registro con email repetido → 409.
- Abrir `/api/auth/register` en el navegador devuelve `405 Method Not Allowed`
  (el navegador hace GET; la ruta solo acepta POST). Es normal: significa que la ruta existe.

### Productos — `/api/products` (🔒)

| Método | Ruta | Parámetros | Respuesta |
|---|---|---|---|
| GET | `/` | `search?`, `category?`, `active_only=true`, `sort=name`, `limit=50 (1-200)`, `offset=0` | ProductListOut |
| POST | `/` | body ProductCreate | 201 ProductOut |
| GET | `/{product_id}` | — | ProductOut |
| PUT | `/{product_id}` | body ProductUpdate (parcial) | ProductOut |
| DELETE | `/{product_id}` | — | 204 (borrado lógico: `is_active=false`) |

- **ProductCreate:** `{ name, category?, supplier?, price>=0, quantity>=0 (stock inicial), min_stock>=0, lead_time_days>=0 }`
- **ProductUpdate:** todos opcionales (`name`, `category`, `supplier`, `price`, `min_stock`, `lead_time_days`). **No** cambia stock (para eso, movimientos de inventario).
- **ProductOut:** `{ id, name, category, supplier, price, stock_quantity, min_stock, lead_time_days, is_active }`
- **ProductListOut:** `{ items[], total, limit, offset }`
- `sort`: `name`, `-name`, `price`, `-price`, `stock`, `-stock`, `created`, `-created`.
- `category`/`supplier` son texto libre; categorías y proveedores se crean
  automáticamente por nombre (catálogos internos).

### Ventas — `/api/sales` (🔒)

| Método | Ruta | Parámetros | Respuesta |
|---|---|---|---|
| POST | `/` | body SaleCreate | 201 SaleOut |
| POST | `/import` | `multipart/form-data` (campo `file`), query `affects_inventory=false` | 201 ImportOut |
| GET | `/` | `product_id?`, `date_from?`, `date_to?`, `limit=50 (1-500)`, `offset=0` | SaleListOut |

- **SaleCreate:** `{ product_id, sale_date (YYYY-MM-DD), quantity>0, unit_price? (si falta, usa el precio del producto) }`
- **SaleOut:** `{ id, product_id, product_name, sale_date, quantity, unit_price, total_amount, source ("MANUAL"/"CSV"), affects_inventory }`
- Venta manual descuenta inventario (trigger). Si el stock es insuficiente → **422**.
- **CSV (`/import`)**: columnas (encabezados sin distinguir mayúsculas):
  - `product` (o `product_name`/`nombre`) **o** `product_id`
  - `date` (o `sale_date`/`fecha`): `YYYY-MM-DD` o `DD/MM/YYYY`
  - `quantity` (o `cantidad`): entero > 0
  - `unit_price` (o `price`/`precio`): opcional, decimal ≥ 0
  - Por defecto **no** descuenta stock (histórico); `?affects_inventory=true` para descontar.
- **ImportOut:** `{ id, file_name, total_rows, imported_rows, error_rows, status ("PROCESSING"/"COMPLETED"/"FAILED"), errors[{ row, field, message }] }`

### Inventario — `/api/inventory` (🔒)

| Método | Ruta | Parámetros | Respuesta |
|---|---|---|---|
| GET | `/` | `status?` (NORMAL/BAJO/AGOTADO), `category?`, `search?`, `sort=name`, `limit=50 (1-200)`, `offset=0` | InventoryListOut |
| POST | `/movements` | body MovementCreate | 201 MovementOut |
| GET | `/{product_id}` | — | InventoryItemOut |
| GET | `/{product_id}/movements` | `limit=50`, `offset=0` | MovementListOut |

- **InventoryItemOut:** `{ product_id, name, category, supplier, price, stock_quantity, min_stock, lead_time_days, status }`
- **MovementCreate:** `{ product_id, movement_type ("PURCHASE"|"ADJUSTMENT"), quantity_change (int, no 0; PURCHASE>0), notes? }`
  - Sirve para reponer stock o corregirlo (el trigger recalcula el stock).
- **MovementOut:** `{ id, product_id, movement_type, quantity_change, stock_after, notes, created_at }`

### Análisis histórico — `/api/analytics` (🔒)

| Método | Ruta | Parámetros | Respuesta |
|---|---|---|---|
| GET | `/sales` | `period=daily` (daily/weekly/monthly/yearly), `date_from?`, `date_to?`, `product_id?` | SalesSeriesOut |
| GET | `/top-products` | `order=top` (top/bottom), `limit=10 (1-100)`, `date_from?`, `date_to?` | ProductRankingListOut |

- Por defecto el rango es **últimos 30 días** si no se envía `date_from`/`date_to`.
- **SalesSeriesOut:** `{ period, date_from, date_to, series[{ period, units, revenue }] }`
- **ProductRankingListOut:** `{ order, items[{ product_id, name, units, revenue }] }`

### Predicción — `/api/forecasting` (🔒)

| Método | Ruta | Parámetros | Respuesta |
|---|---|---|---|
| POST | `/` | body ForecastRequest | 201 ForecastOut |
| GET | `/` | `product_id` (requerido), `limit=20` | ForecastListOut |

- **ForecastRequest:** `{ product_id, forecast_days? (1-365, def. 30), model? ("LINEAR_REGRESSION"|"MOVING_AVERAGE", def. MOVING_AVERAGE) }`
- **ForecastOut:** `{ id, product_id, model_type, history_days, forecast_days, forecast_start, predicted_demand, confidence (0-1), daily_prediction[{ date, value }] }`
- **RNF-04:** exige ≥ 30 días de historial; si no → **422**.
- **RNF-03:** la predicción es cálculo en memoria (rápida, < 2 s).

### Recomendación — `/api/recommendations` (🔒)

| Método | Ruta | Parámetros | Respuesta |
|---|---|---|---|
| POST | `/` | body RecommendationRequest | 201 RecommendationOut |
| GET | `/` | `product_id` (requerido), `limit=20` | RecommendationListOut |

- **RecommendationRequest:** `{ product_id, forecast_days? }`
- Si no hay predicción reciente, la genera antes de recomendar.
- **RecommendationOut:** `{ id, product_id, forecast_id, current_stock, min_stock, lead_time_days, predicted_demand, coverage_days, suggested_quantity, urgency ("BAJO"|"MEDIO"|"ALTO"), justification, created_at }`
- **Criterio de urgencia:** agotado → ALTO; cobertura < lead time → ALTO; cobertura
  < 2×lead time o stock < stock mínimo → MEDIO; resto → BAJO.
- Cantidad sugerida = `max(0, demanda_diaria × lead_time + stock_mínimo − stock_actual)`.

### Dashboard — `/api/dashboard` (🔒)

| Método | Ruta | Parámetros | Respuesta |
|---|---|---|---|
| GET | `/` | `trend_days=30 (1-365)` | DashboardOut |

- **DashboardOut:** `{ total_products, total_stock, inventory_value, current_period{ units_sold, revenue }, low_stock_products[{ product_id, name, stock_quantity, min_stock, status }], trend[{ date, units }] }`

### Alertas — `/api/alerts` (🔒)

| Método | Ruta | Parámetros | Respuesta |
|---|---|---|---|
| GET | `/` | `status?` (PENDING/REVIEWED), `limit=50`, `offset=0` | AlertListOut |
| POST | `/generate` | — | GenerateAlertsOut `{ created }` |
| PATCH | `/{alert_id}/review` | — | AlertOut |

- `/generate` escanea `v_inventory` y crea alertas pendientes para productos en
  BAJO/AGOTADO (una sola pendiente por producto), enriquecidas con la última
  predicción/recomendación si existen. Requiere invocarse (no es automático).
- **AlertOut:** `{ id, product_id, recommendation_id, current_stock, min_stock, estimated_demand, recommended_quantity, status, reviewed_at, created_at }`

---

## 8. Requerimientos cubiertos

| Req | Estado | Dónde |
|---|---|---|
| RF-01/02/03 registro, login/logout, aislamiento por negocio | ✅ | módulo `auth` |
| RF-04/05 CRUD + borrado lógico de productos | ✅ | módulo `products` |
| RF-06/07/08 venta manual, CSV, actualización de inventario | ✅ | módulo `sales` + triggers |
| RF-09 inventario con estado/orden/filtro | ✅ | módulo `inventory` + `v_inventory` |
| RF-10/11 análisis por período, más/menos vendidos | ✅ | módulo `analytics` |
| RF-12 predicción + serie diaria | ✅ | módulo `forecasting` |
| RF-13 recomendación con justificación y urgencia | ✅ | módulo `recommendations` |
| RF-14 dashboard de KPIs | ✅ | módulo `dashboard` |
| RF-15 alertas y marcado de revisadas | ✅ | módulo `alerts` |
| RNF-04 mín. 30 días de historial (422) | ✅ | `forecasting/application/handlers.py` |
| RNF-06 códigos HTTP | ✅ | `shared/api/error_handlers.py` |
| RNF-07 monolito modular sin ciclos | ✅ | estructura de módulos |
| RNF-09 tests de servicios principales | ✅ | `backend/tests/` (lógica pura) |

---

## 9. Cómo levantar

### Local

```powershell
# desde backend/, con venv fuera de OneDrive
pip install -r requirements.txt
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

- Ejecutar `db/schema.sql` en Supabase antes.
- Crear `backend/.env` (plantilla en `.env.example` / README).
- Swagger: `http://127.0.0.1:8000/docs`.
- Tests: `python -m pytest` (no requieren BD).

### Producción — Render (plan gratuito)

**URL pública:** `https://cantinapp.onrender.com`
**Repositorio:** `https://github.com/juanjo380/cantinapp` (rama `main`).

**Servicio:** tipo **Web Service** en Render, conectado al repo de GitHub.

| Campo | Valor |
|---|---|
| Language | Python 3 |
| Root Directory | `backend` (sin `/app` ni barra final) |
| Build Command | `pip install -r requirements.txt` |
| Start Command | `python -m uvicorn app.main:app --host 0.0.0.0 --port $PORT` |
| Instance Type | Free |
| Health Check Path | `/health` |
| Auto-Deploy | Activo: cada push a `main` redespliega (solo si cambian archivos dentro de `backend/`) |

**Variables de entorno en Render** (se cargan en el panel *Environment*, no se
sube el `.env`):

| Variable | Valor en producción |
|---|---|
| `DB_HOST` | `aws-0-us-east-1.pooler.supabase.com` (pooler de Supabase) |
| `DB_PORT` | `5432` (pooler en modo sesión) |
| `DB_NAME` | `postgres` |
| `DB_USER` | `postgres.<project-ref>` |
| `DB_PASSWORD` | contraseña de la BD (secreto, no se documenta aquí) |
| `DB_USE_TRANSACTION_POOLER` | `false` |
| `DB_SSL` | `true` |
| `DB_POOL_SIZE` / `DB_MAX_OVERFLOW` | `5` / `5` |
| `DB_ECHO` | `false` |
| `PYTHON_VERSION` | `3.11.9` |
| `JWT_SECRET` | **Pendiente de definir** (valor largo y aleatorio) |
| `CORS_ORIGINS` | **Pendiente**: lista JSON con el origen del frontend, ej. `["http://localhost:5173","https://tu-frontend.vercel.app"]` |

**Verificación del despliegue:** el log muestra `Application startup complete`
(el `SELECT 1` del lifespan pasó, o sea que conecta con Supabase) y
`Your service is live`. Comprobar con:
- `https://cantinapp.onrender.com/health`
- `https://cantinapp.onrender.com/health/db`
- `https://cantinapp.onrender.com/docs`

Los `404` en `GET /` y `HEAD /` de los logs son normales: la app no define ruta raíz.

**Limitaciones del plan gratuito:**
- El servicio se **duerme tras 15 minutos sin tráfico**; la primera petición
  después tarda entre 30 y 60 segundos (cold start). El frontend debe mostrar
  estado de carga y no tratarlo como error.
- Los límites de los planes gratuitos cambian: confirmar en la página de
  precios de Render.
- El plan gratuito de Supabase también puede pausar proyectos tras un periodo
  largo sin actividad.

**Archivos que no deben estar en el repo** (`.gitignore` en la raíz):
```
venv/
.venv/
node_modules/
__pycache__/
.pytest_cache/
.env
```
Si ya se subieron, quitarlos del índice con `git rm -r --cached <ruta>`.

**Estructura prevista del repo (monorepo):**
```
cantinapp/
├── backend/     # Render: Root Directory = backend
├── frontend/    # Vercel/Netlify: Root Directory = frontend
├── db/
└── README.md
```

### Pendientes de seguridad

- **Rotar la contraseña de la BD en Supabase** y actualizar `DB_PASSWORD` en
  Render y en el `.env` local (se compartió en texto plano durante la
  configuración y podría estar en el historial de GitHub si el `.env` se subió).
- **Definir `JWT_SECRET` en Render.** Si no se define, se usa el valor por
  defecto `dev-secret-change-me`, que es público en el código y permitiría
  falsificar tokens.
- **Restringir `CORS_ORIGINS`** al origen real del frontend (el valor por
  defecto `["*"]` permite cualquier origen). `allow_credentials` está en
  `False`, coherente con autenticación por header Bearer.
- `/health/db` es público y expone nombre de la BD, versión del servidor y
  número de tablas; protegerlo o retirarlo antes de usar datos reales.
- `scripts/check_db.py` importa `app.infrastructure.database` (ruta antigua);
  la correcta es `app.shared.infrastructure.database`. No afecta al despliegue.

---

## 10. Notas para el frontend

- **URL base de la API:** `https://cantinapp.onrender.com` (guardarla en una
  variable de entorno del frontend, ej. `VITE_API_URL`, nunca fija en el código).
- Usar siempre `https://` (un frontend en HTTPS no puede llamar a un backend HTTP).
- Autenticación Bearer; guardar el token y enviarlo en `Authorization`.
- Las rutas llevan prefijo `/api` (ej. `POST /api/auth/register`).
- Todo el aislamiento lo garantiza el backend: no enviar `business_id`.
- Fechas en ISO `YYYY-MM-DD`.
- El stock no se edita directo: usar `POST /api/inventory/movements`.
- Para que la predicción funcione debe haber ≥ 30 días de historial (cargar CSV
  histórico).
- Recomendación y alertas dependen de que exista una predicción; la recomendación
  la genera sola, las alertas requieren `POST /api/alerts/generate`.
- CORS configurable vía `CORS_ORIGINS` en Render (añadir el origen exacto del
  frontend: esquema + dominio + puerto, sin barra final).
- Ejemplo de llamada:
  ```js
  const API_URL = import.meta.env.VITE_API_URL;
  const res = await fetch(`${API_URL}/api/auth/register`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ business_name, email, password, full_name }),
  });
  ```