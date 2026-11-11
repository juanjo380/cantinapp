# Memoria técnica — CantinAPP (backend)

Documento de contexto acumulado del proyecto. Nivel técnico general, con el
detalle necesario para construir el frontend sobre esta API.

Última actualización (2026-11-11): **ventas y métricas por sede**, sede asignada a cada persona del
equipo, **solo el dueño** edita negocio y sedes, registro de **cuenta sin negocio** para invitados,
**reactivar productos** y **buscador de productos** en modal. Antes (2026-11-08): CSV sin duplicados,
predicción semanal + AUTO, trabajo diario y datos de ejemplo. Bitácora y pendientes en la **sección 12**.

> ⚠️ **Pendiente bloqueante antes de desplegar:** ejecutar en el SQL Editor de Supabase, en
> orden, `db/migrations/001` → … → `008` (reportadas como ejecutadas el 2026-11-08) y **`009`** (ver sección 4).
> **El backend se despliega después de las migraciones**: sin ellas responde 500.
> **Antes del deploy, crear `CRON_SECRET` (≥ 32 caracteres) en Render**: fuera de development la app
> no arranca sin él. Correos reales: `MAIL_BACKEND=brevo`, `BREVO_API_KEY`, `MAIL_FROM` y
> `FRONTEND_URL` en Render. Secrets de GitHub `CANTINAPP_API_URL` y `CRON_SECRET` (secciones 9 y 12).

---

## 1. Qué es el proyecto

SaaS para pymes que gestiona inventario y predice demanda a partir de ventas
históricas. Un **negocio (tenant)** tiene usuarios; cada usuario solo ve los
datos de su negocio. Alcance v0.1 (doc `MinimoReq.md`): login, productos,
ventas (manual + CSV), inventario, análisis, predicción, recomendación
(MUST) + dashboard y alertas (SHOULD).

- **Monorepo:** `backend/` (API FastAPI) y `frontend/` (SPA React) conviven en el
  mismo repositorio; el frontend consume esta API desplegada (ver sección 11).
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
| `MAIL_BACKEND` | `console` (por defecto: solo log) o `brevo` (exige `BREVO_API_KEY`) |
| `BREVO_API_KEY`, `MAIL_FROM`, `MAIL_FROM_NAME` | API de Brevo y remitente verificado en su panel |
| `FRONTEND_URL` | Base de los enlaces de los correos (`http://localhost:5173` por defecto) |
| `CRON_SECRET` | Secreto del header `X-Cron-Secret` del trabajo diario. **Obligatorio (≥ 32 caracteres) fuera de development**; en development, si falta, el endpoint responde 403 siempre |

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

**Tablas:** `businesses`, `users`, `user_consents`, `business_members`, `business_locations`,
`email_codes`, `business_invitations`, `categories`, `suppliers`, `products`, `product_components`,
`sales_imports`, `sales`, `inventory_movements`, `forecasts`,
`recommendations`, `product_cooccurrences`, `alerts`.

**Migraciones** (`db/migrations/`, se ejecutan a mano en el SQL Editor sobre una BD
que ya tiene `schema.sql`; `schema.sql` incluye las tablas para instalaciones nuevas):

| Archivo | Qué hace | Producción |
|---|---|---|
| `001_product_cooccurrences.sql` | Tabla de pares A→B (`peaks`, `hits`, `score`), FK compuestas, RLS y `REVOKE` a `anon`/`authenticated` | **PENDIENTE de ejecutar** |
| `002_user_consents.sql` | Bitácora de autorizaciones del registro (términos, privacidad, cookies, uso anónimo para ML) con versión y fecha; RLS | **PENDIENTE de ejecutar** (antes de desplegar el backend: sin ella `/register` da 500) |
| `003_business_profile_members.sql` | Perfil del negocio y del usuario, `business_members` (usuario ↔ negocios con rol OWNER/ADMIN/MEMBER, backfill del usuario actual como OWNER), `business_locations` (sedes), `users.business_id` pasa a «último negocio usado» | **PENDIENTE de ejecutar** (después de 001 y 002, antes del backend: sin ella todo da 500) |
| `004_email_codes_invitations.sql` | `users.password_changed_at` (invalida tokens anteriores), `email_codes` (códigos de recuperación, solo hash), `business_invitations` (enlace + código de seguridad) | **PENDIENTE de ejecutar** (después de 003, antes del backend: sin ella todo da 500) |
| `005_sales_dedup.sql` | `sales_imports.file_hash` + `duplicate_rows`, `sales.row_hash` con índice único parcial `(business_id, row_hash)` y **backfill** de las ventas CSV existentes | **PENDIENTE** (sin ella la carga de CSV da 500) |
| `006_forecast_backtest.sql` | CHECK de `forecasts.model_type` con `SEASONAL_WEEKLY`; `requested_model`, `backtest_wape`, `backtest_mae` | **PENDIENTE** (sin ella toda predicción nueva falla) |
| `007_alerts_notified.sql` | `alerts.notified_at` (correo-resumen diario) | **PENDIENTE** (sin ella el trabajo diario da 500) |
| `008_demo_data.sql` | CHECK de `sales.source` con `DEMO`; `products.is_demo` | **PENDIENTE** (sin ella `/api/demo` da 500) |
| `009_sedes_ventas_equipo.sql` | `user_consents.business_id` admite NULL (cuentas sin negocio); `location_id` en `sales`, `business_members` y `business_invitations` con FK compuesta `(business_id, location_id)` → `business_locations` (en invitaciones `ON DELETE CASCADE`); índice parcial de ventas por sede | **PENDIENTE** (antes del backend: `get_current_user` lee `business_members.location_id`, sin ella todo da 500). **No** es idempotente: correrla dos veces falla (sin efectos, va en una transacción) |
| `010_compuestos.sql` | `businesses.composites_enabled` (default false); tabla `product_components` (receta: `product_id`, `component_id`, `quantity` entero > 0, FK compuestas `ON DELETE CASCADE`, RLS + `REVOKE`); reemplaza `fn_sale_inventory` y `fn_sale_restore_inventory` (descuentan/devuelven componentes si el negocio lo activó) y `v_inventory` (stock de un compuesto = cuántos se pueden armar) | **PENDIENTE** (después de 009, antes del backend: login y `/auth/me` leen `businesses.composites_enabled`, sin ella dan 500). **No** es idempotente |

Todas las migraciones 005–008 son idempotentes (`IF NOT EXISTS`, `DROP CONSTRAINT IF EXISTS`).
**Ninguna se ha probado contra una BD real**: el backfill de la 005 replica en SQL la fórmula de
`sales/domain/dedup.py` (`producto|AAAA-MM-DD|cantidad|precio con 2 decimales|n`).

Estado reportado por el autor (2026-11-08): 001–008 ya corrieron en Supabase. Faltan la 009 y la 010.

**Multi-negocio (desde 003):** el JWT lleva el negocio activo (`bid`, puede ser null) y `get_current_user` verifica en **cada request** que el usuario sea miembro (`business_members`); si no, **403** (no 401). Cambiar de negocio = `POST /api/auth/switch` (token nuevo). Nuevos endpoints: `PUT /api/auth/me`, `PUT /api/auth/password`, `POST /api/auth/switch`, `POST /api/auth/businesses`; módulo `business`: `GET|PUT /api/business`, CRUD `/api/business/locations`, `/api/business/members` (cambiar rol, quitar/salirse; desde 004 el alta es solo por `/api/business/invitations`). Desde 2026-11-11 perfil y sedes los edita solo el dueño; dueño y admin gestionan el equipo; el dueño no se puede quitar ni cambiar.

Verificación: `python -m scripts.check_db` (desde `backend/`) debe decir "Esquema completo".

**Vistas:** `v_inventory` (estado NORMAL/BAJO/AGOTADO calculado; desde 010, para un compuesto el stock es
`MIN(stock del componente / cantidad)`),
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
   Desde 010, si el producto vendido tiene receta y el negocio tiene `composites_enabled`, el trigger
   descuenta cada componente (`-cantidad × unidades de receta`) en vez del producto; el CHECK de stock no
   negativo protege cada componente (venta manual → 422, CSV → error de fila «Stock insuficiente»).
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

- **RF-01/02:** registro crea negocio + usuario **dueño (OWNER)** + 3 filas de consentimiento
  (desde 009, sin `business_name` crea **solo la cuenta**, sin negocio ni membresía, para quien
  entrará por invitación; sus consentimientos quedan con `business_id` NULL)
  (`TERMS`, `PRIVACY` —incluye cookies— y `ML_ANONYMOUS`, versión `LEGAL_VERSION`); login devuelve JWT.
  Términos y privacidad son obligatorios (si no, 422). La versión debe coincidir con `UPDATED`
  de `frontend/src/components/auth/LegalDialog.jsx`.
- **JWT** (`core/security.py`): HS256, claims `sub` (id usuario), `bid` (negocio **activo**,
  puede ser `null`), `iat`, `exp`. Firma HMAC-SHA256 con `JWT_SECRET` (obligatorio y de ≥ 32
  caracteres si `ENVIRONMENT` ≠ `development`: la app no arranca sin él).
- **Hash de contraseña:** PBKDF2-SHA256, 260k iteraciones, sal aleatoria. Bloqueo temporal tras
  5 logins fallidos (en memoria por proceso; recuperar la contraseña lo levanta).
- **Cerrar otras sesiones (desde 004):** `get_current_account` rechaza (401) los tokens cuyo `iat`
  sea anterior a `users.password_changed_at`; cambiar o recuperar la contraseña la actualiza.
  Códigos de correo e invitaciones se guardan como HMAC con `JWT_SECRET` (rotarlo los anula).
- **Multi-negocio (desde 003):** un usuario pertenece a varios negocios vía `business_members`
  con rol `OWNER` / `ADMIN` / `MEMBER` (un solo dueño). `users.business_id` = último negocio usado.
- **Multitenancy (RNF-01):** `shared/api/dependencies.py`:
  - `get_current_account`: valida token y usuario (perfil, cambio de negocio).
  - `get_current_user`: además verifica **en cada request** que el usuario sea miembro del
    negocio del token y expone `business_id`, `role` y `location_id` (sede asignada; siempre `None`
    para el dueño). `CurrentUser.scoped_location(pedida)` devuelve la sede asignada o, si no tiene, la
    pedida (`None` = todas): así se filtran ventas, análisis y dashboard. **Todos** los endpoints de negocio lo usan
    y filtran por ese `business_id`. Nunca se acepta `business_id` desde el cliente.
- Errores: 401 si falta/expira/está mal el token; **403** si no hay negocio activo o ya no es
  miembro (la sesión sigue válida: el cliente debe elegir otro); 404 en recursos de otro negocio
  (no se revela su existencia).
- **Permisos** (módulo `business`, en los handlers, desde 2026-11-11): **solo el dueño** edita el perfil
  del negocio, las sedes y la autorización de datos (ML); dueño y admin gestionan el equipo
  (invitar, rol, sede, quitar); el miembro solo consulta y puede salirse. Al dueño no se le cambia el
  rol ni se le quita. Un admin **con sede** solo invita a su sede y solo gestiona a gente de su sede.

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
| POST | `/register` | 🔓 | `{ business_name? (vacío = cuenta sin negocio), email, password (min 8), full_name?, accept_terms, accept_privacy, allow_ml_data }` | 201 AuthResponse |
| POST | `/login` | 🔓 | `{ email, password }` | AuthResponse (abre el último negocio usado) |
| POST | `/logout` | 🔒 | — | 204 (JWT sin estado: el cliente descarta el token) |
| GET | `/me` | 🔒 | — | SessionOut (negocio del token; `business_id: null` si ya no es miembro) |
| PUT | `/me` | 🔒 | `{ full_name?, phone?, job_title? }` | SessionOut |
| PUT | `/password` | 🔒 | `{ current_password, new_password (min 8) }` | AuthResponse con **token nuevo**: cierra las demás sesiones (422 si la actual no coincide) |
| POST | `/password/forgot` | 🔓 | `{ email }` | 202 siempre igual; si la cuenta existe envía un código de 6 dígitos (vence en 5 min, uno por minuto) |
| POST | `/password/reset` | 🔓 | `{ email, code, new_password }` | 204; 422 si el código es malo o venció (5 intentos por código) |
| POST | `/switch` | 🔒 | `{ business_id }` | AuthResponse con **token nuevo** (404 si no es miembro) |
| POST | `/businesses` | 🔒 | `{ name }` | 201 AuthResponse: crea negocio (dueño) y lo activa |

- **SessionOut:** `{ user{ id, business_id, email, full_name, phone, job_title }, business_id, business_name, role, profile_completed, businesses[{ business_id, business_name, role, profile_completed, location_id }] }` (`location_id` = sede asignada en ese negocio; null = todas)
- **AuthResponse:** SessionOut + `{ token, token_type:"bearer" }`.
- `profile_completed`: el negocio tiene tipo, teléfono, dirección, ciudad y departamento, y el usuario tiene nombre.

### Negocio — `/api/business` (🔒, negocio activo)

| Método | Ruta | Cuerpo | Respuesta |
|---|---|---|---|
| GET / PUT | (raíz) | `{ name?, legal_name?, tax_id?, business_type?, phone?, email?, address?, city?, department?, composites_enabled? }` | BusinessOut (incluye `composites_enabled`) |
| GET / POST | `/locations` | `{ name, address?, city?, phone?, is_main }` | sedes (la primera queda principal) |
| PUT / DELETE | `/locations/{id}` | igual que POST | LocationOut / 204 |
| GET | `/members` | — | MemberOut[] (al equipo se entra solo por invitación) |
| GET / POST | `/invitations` | `{ email, role: ADMIN\|MEMBER, location_id? }` (cuenta ya registrada; dueño o admin) | POST: 201 con `code` de seguridad (solo esta vez); envía el enlace al correo. 404 sin cuenta, 409 si ya es miembro, 503 si el correo falla |
| DELETE | `/invitations/{id}` | — | 204 (anular) |
| GET | `/invitations/preview?token=` | sesión de la cuenta invitada (sin negocio) | `{ business_name, role, invited_by_name, expires_at }`; 403 si es para otro correo |
| POST | `/invitations/accept` | `{ token, code }` (sesión de la cuenta invitada) | AuthResponse ya dentro del negocio; 5 intentos de código, vence en 48 h |
| PATCH / DELETE | `/members/{user_id}` | `{ role, location_id }` (se envían juntos; `location_id` null = todas las sedes) | MemberOut (incluye `location_id`) / 204 (salirse uno mismo está permitido) |

- `tax_id` (NIT) se normaliza y, si trae dígito de verificación, se valida (módulo 11 de la DIAN).
- `business_type`: `TIENDA, MINIMERCADO, CANTINA_ESCOLAR, CAFETERIA, RESTAURANTE, PANADERIA, DROGUERIA, OTRO` (debe coincidir con `BUSINESS_TYPES` de `frontend/src/pages/Profile.jsx`).
- Desde 009 **cada venta guarda su sede** (`sales.location_id`, NULL = sin sede, como las anteriores); el
  **inventario sigue siendo del negocio**. Predicción y reabastecimiento usan las ventas de todo el negocio.
- `GET|PUT|POST|DELETE` de perfil y sedes: solo el dueño (403 al resto). Borrar una sede con ventas o
  personas asignadas → 409; sus invitaciones pendientes se borran en cascada.
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
| POST | `/import` | `multipart/form-data` (campo `file`) | 201 ProductImportOut `{ file_name, total_rows, imported_rows, error_rows, status, errors[] }` |
| GET | `/import/template` 🔓 | — | `plantilla-productos.csv` (UTF-8 con BOM, `;`, 3 filas de ejemplo) |
| GET | `/composites` | — | CompositeOut[] `{ product_id, name, price, available, components[{ component_id, name, quantity, stock_quantity }] }` |
| PUT | `/{product_id}/components` | `{ components: [{ component_id, quantity>=1 }] }` (máx. 50, sin repetidos; vacía = deja de ser compuesto) | 204; 422 si la sección está apagada, si es componente de sí mismo o si la receta quedaría anidada; 404 si un componente no existe o está inactivo |

- **CSV de productos:** `nombre`/`name` y `precio`/`price` obligatorias; opcionales `categoria`, `proveedor`, `stock_inicial`/`quantity`, `stock_minimo`/`min_stock`, `dias_abastecimiento`/`lead_time_days`. Nombres ya activos o repetidos en el archivo se reportan como error de fila (no se actualizan).
- **Ambos CSV (productos y ventas):** separador `,` o `;`, UTF-8 o Windows-1252 (Excel), coma decimal (`2500,50`), máximo 5 MB. Utilidades en `shared/application/csv_utils.py` y `shared/api/uploads.py`.

- **ProductCreate:** `{ name, category?, supplier?, price>=0, quantity>=0 (stock inicial), min_stock>=0, lead_time_days>=0 }`
- **ProductUpdate:** todos opcionales (`name`, `category`, `supplier`, `price`, `min_stock`, `lead_time_days`, `is_active` — `true` reactiva un producto desactivado). **No** cambia stock (para eso, movimientos de inventario).
- **ProductOut:** `{ id, name, category, supplier, price, stock_quantity, min_stock, lead_time_days, is_active }`
- **ProductListOut:** `{ items[], total, limit, offset }`
- `sort`: `name`, `-name`, `price`, `-price`, `stock`, `-stock`, `created`, `-created`.
- **Compuestos (desde 010):** un solo nivel (un componente no puede tener receta, y un producto que ya es
  componente no puede volverse compuesto). Cualquier miembro edita recetas, como el resto de productos.
  La venta manual de un compuesto omite la validación de stock propio (`has_recipe`) y la deja al trigger.
- `category`/`supplier` son texto libre; categorías y proveedores se crean
  automáticamente por nombre (catálogos internos).

### Ventas — `/api/sales` (🔒)

| Método | Ruta | Parámetros | Respuesta |
|---|---|---|---|
| POST | `/` | body SaleCreate | 201 SaleOut |
| POST | `/import` | `multipart/form-data` (campo `file`), query `affects_inventory=false`, `skip_duplicates=true`, `confirm_reimport=false`, `location_id?` (sede de todas las filas) | 201 ImportOut; **409** si ese mismo archivo ya se importó (salvo `confirm_reimport=true`) |
| GET | `/import/template` 🔓 | — | `plantilla-ventas.csv` (UTF-8 con BOM, `;`, fechas DD/MM/AAAA y AAAA-MM-DD) |
| GET | `/` | `product_id?`, `location_id?`, `date_from?`, `date_to?`, `limit=50 (1-500)`, `offset=0` | SaleListOut (cada venta trae `location_id` y `location_name`) |

- **Sede (desde 009):** `SaleCreate` acepta `location_id?`. Si el usuario tiene sede asignada, el backend usa
  **siempre** la suya (al registrar, importar y listar) e ignora la pedida. Una sede de otro negocio → 404 (FK compuesta).

- **SaleCreate:** `{ product_id, sale_date (YYYY-MM-DD), quantity>0, unit_price? (si falta, usa el precio del producto) }`
- **SaleOut:** `{ id, product_id, product_name, sale_date, quantity, unit_price, total_amount, source ("MANUAL"/"CSV"/"DEMO"), affects_inventory }`
- Venta manual descuenta inventario (trigger). Si el stock es insuficiente → **422**.
- **CSV (`/import`)**: columnas (encabezados sin distinguir mayúsculas):
  - `product` (o `product_name`/`nombre`/`producto`) **o** `product_id`
  - `date` (o `sale_date`/`fecha`): `YYYY-MM-DD`, `DD/MM/YYYY` o `DD-MM-YYYY`
  - `quantity` (o `cantidad`): entero > 0
  - `unit_price` (o `price`/`precio`): opcional, decimal ≥ 0
  - Por defecto **no** descuenta stock (histórico); `?affects_inventory=true` para descontar.
- **ImportOut:** `{ id, file_name, total_rows, imported_rows, error_rows, duplicate_rows, status ("PROCESSING"/"COMPLETED"/"FAILED"), errors[{ row, field, message }] }`.
  `total_rows = imported_rows + error_rows + duplicate_rows`.
- **Sin duplicados (desde 005):** dos niveles.
  1. **Archivo:** sha256 del contenido en `sales_imports.file_hash`. Si ya hay una carga COMPLETED de ese
     archivo en el negocio → 409 con la fecha; el cliente reintenta con `confirm_reimport=true`.
  2. **Fila:** `row_hash` = sha256 de `producto|fecha|cantidad|precio|n`, con `n` = cuántas veces apareció antes
     esa misma fila en el archivo (`sales/domain/dedup.py`). Reimportar es idempotente, pero 3 ventas iguales
     el mismo día entran las 3. Índice único parcial por negocio (protege también cargas simultáneas).
  - `skip_duplicates=false`: inserta todo con `row_hash = NULL` (duplicado a propósito, no bloquea futuras cargas).
  - Ventas manuales no llevan huella. El backfill numera `n` por negocio: si un CSV ya se había importado dos
    veces, sus copias quedan con `n` 0 y 1.

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
| GET | `/sales` | `period=daily` (daily/weekly/monthly/yearly), `date_from?`, `date_to?`, `product_id?`, `location_id?` | SalesSeriesOut |
| GET | `/top-products` | `order=top` (top/bottom), `limit=10 (1-100)`, `date_from?`, `date_to?`, `location_id?` | ProductRankingListOut |

- `location_id?` también en `/classification`. Con sede asignada se fuerza la del usuario (igual en el dashboard).

- Por defecto el rango es **últimos 30 días** si no se envía `date_from`/`date_to`.
- **SalesSeriesOut:** `{ period, date_from, date_to, series[{ period, units, revenue }] }`
- **ProductRankingListOut:** `{ order, items[{ product_id, name, units, revenue }] }`

### Predicción — `/api/forecasting` (🔒)

| Método | Ruta | Parámetros | Respuesta |
|---|---|---|---|
| POST | `/` | body ForecastRequest | 201 ForecastOut |
| GET | `/` | `product_id` (requerido), `limit=20` | ForecastListOut |
| GET | `/accuracy` | `product_id` (requerido) | AccuracyOut |

- **ForecastRequest:** `{ product_id, forecast_days? (1-365, def. 30), model? ("AUTO"|"SEASONAL_WEEKLY"|"LINEAR_REGRESSION"|"MOVING_AVERAGE", def. **AUTO**) }`
- **ForecastOut:** `{ id, product_id, model_type, history_days, forecast_days, forecast_start, predicted_demand, confidence (0-1), daily_prediction[{ date, value }], requested_model, backtest_wape, backtest_mae }`
  - `model_type` = modelo usado (con AUTO, el ganador); `requested_model` = lo pedido (NULL en predicciones anteriores a 006).
- **Modelos** (`forecasting/domain/models.py`, Python puro):
  - `MOVING_AVERAGE`: promedio de 7 días. `LINEAR_REGRESSION`: mínimos cuadrados.
  - `SEASONAL_WEEKLY`: nivel = promedio de 28 días × factor del día de la semana (promedio de ese día / nivel),
    encogido hacia 1 con pocas semanas. Se descartó Holt-Winters: pide ≥ 2 temporadas y ajustar α, β, γ; con
    30 días sobreajusta.
  - `AUTO`: backtest con los últimos 14 días; gana el menor **WAPE** (empate: MAE, luego el más simple:
    promedio → semanal → regresión). No MAPE: explota con días en 0.
  - **confidence = 1 − WAPE** del backtest (0..1). Si los 14 días de prueba no tuvieron ventas, WAPE no existe y
    se usa `1 / (1 + MAE)`. Reemplaza las fórmulas anteriores (1 − coef. de variación y R²).
- **AccuracyOut:** `{ product_id, evaluated, predicted_total, actual_total, wape, mae, accuracy, items[{ forecast_id, model_type, forecast_start, forecast_end, predicted_total, actual_total, wape, mae, accuracy }] }`
  - Solo predicciones con periodo cumplido (último día < hoy), comparando `daily_prediction` contra ventas reales
    (0 los días sin ventas). Un periodo recalculado varias veces cuenta una vez (la más reciente). Máx. 20.
  - `accuracy = 1 − WAPE` (None si en el periodo no hubo ventas). `evaluated = 0` → estado vacío en el frontend.
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

#### Co-ocurrencia temporal de picos (Fase 1, sin IA)

| Método | Ruta | Parámetros | Respuesta |
|---|---|---|---|
| GET | `/cooccurrence` | `product_id` (requerido) | CoOccurrenceListOut |
| POST | `/cooccurrence/recompute` | — | 202 (calcula en segundo plano) |

- **CoOccurrenceListOut:** `{ product_id, items[{ related_product_id, related_product_name, score (0-1), hits, peaks, computed_at }] }`, ordenado por score desc.
- Tabla `product_cooccurrences` (migración `db/migrations/001_product_cooccurrences.sql`). Cada recálculo reemplaza los pares del negocio.
- **Algoritmo** (`recommendations/domain/cooccurrence.py`): serie diaria densa (0 sin ventas, máx. 365 días).
  Pico de A = venta > media de los 14 días anteriores y ≥ media + 2σ. B "sube" si en el día +1..+3
  vende más que su propia media de 14 días. `score = coincidencias / picos de A`; se descartan pares con < 3 coincidencias.
- Umbrales por entorno: `COOCCURRENCE_WINDOW_DAYS`, `COOCCURRENCE_SIGMA`, `COOCCURRENCE_MAX_LAG_DAYS`, `COOCCURRENCE_MIN_HITS`.
- Requiere ≥ 30 días de historial (negocio para recalcular, producto para consultar) → si no, **422**.
- Tarea programada: `python -m scripts.recompute_cooccurrence [--business-id <uuid>]` (Render Cron Job, diario).
- Limitación: no descuenta subidas generales del negocio (quincena, festivos).

### Dashboard — `/api/dashboard` (🔒)

| Método | Ruta | Parámetros | Respuesta |
|---|---|---|---|
| GET | `/` | `trend_days=30 (1-365)`, `location_id?` (filtra ventas del mes y tendencia; el stock es del negocio) | DashboardOut |

- **DashboardOut:** `{ total_products, total_stock, inventory_value, current_period{ units_sold, revenue }, low_stock_products[{ product_id, name, stock_quantity, min_stock, status }], trend[{ date, units }] }`

### Alertas — `/api/alerts` (🔒)

| Método | Ruta | Parámetros | Respuesta |
|---|---|---|---|
| GET | `/` | `status?` (PENDING/REVIEWED), `limit=50`, `offset=0` | AlertListOut |
| POST | `/generate` | — | GenerateAlertsOut `{ created }` |
| PATCH | `/{alert_id}/review` | — | AlertOut |

- `/generate` escanea `v_inventory` y crea alertas pendientes para productos en
  BAJO/AGOTADO (una sola pendiente por producto), enriquecidas con la última
  predicción/recomendación si existen. Desde la fase 5 también lo hace el **trabajo diario**.
- **AlertOut:** `{ id, product_id, recommendation_id, current_stock, min_stock, estimated_demand, recommended_quantity, status, reviewed_at, created_at }`
- Alerta `REVIEWED` con `reviewed_by = NULL` = **resuelta sola** (el trabajo diario vio el producto otra vez en NORMAL).

### Trabajo diario — `/api/internal/jobs` (header `X-Cron-Secret`, oculto en Swagger)

| Método | Ruta | Auth | Respuesta |
|---|---|---|---|
| POST | `/daily` | `X-Cron-Secret: <CRON_SECRET>` (sin header **401**; incorrecto o sin `CRON_SECRET` configurado **403**; comparación `hmac.compare_digest`) | `{ businesses, failed, results[{ business_id, ok, resolved, created, cooccurrence_pairs, emailed } \| { business_id, ok:false, error }] }` |

- Para cada negocio con productos activos, con sesiones propias (si uno falla, se registra en el log y se sigue):
  1. resuelve las alertas pendientes cuyo producto volvió a NORMAL;
  2. genera las nuevas (`/generate`);
  3. recalcula co-ocurrencias (se omite si hay < 30 días de historial);
  4. envía **un único correo-resumen al día** a dueño y administradores activos, **solo si hay alertas sin
     avisar** (`alerts.notified_at IS NULL`) y no se envió ya hoy (UTC). Si ningún correo sale, no se marcan y
     se reintenta al día siguiente.
- **No** regenera predicciones (sería una por producto): las alertas usan la última que exista.
- Equivalente por consola: `python -m scripts.run_daily_jobs [--business-id <uuid>]` (sale con 1 si algo falló).
- Programado en `.github/workflows/daily-jobs.yml` (11:00 UTC = 6:00 Colombia, también a mano con
  *Run workflow*). La llamada **despierta Render**; `curl` reintenta 3 veces cada 30 s por el cold start.

### Datos de ejemplo — `/api/demo` (🔒)

| Método | Ruta | Respuesta |
|---|---|---|
| GET | (raíz) | `{ has_demo, can_load, demo_products, demo_sales }` (`can_load`: dueño, negocio sin ventas y sin ejemplo) |
| POST | (raíz) | 201 igual que GET. Solo **OWNER** (si no 403); **409** si ya hay ventas o ya hay datos de ejemplo |
| DELETE | (raíz) | `{ deleted_products }`. Solo OWNER |

- 12 productos `«… (ejemplo)»` (`products.is_demo`) y 90 días de ventas `source = 'DEMO'`, `affects_inventory = false`,
  generados de forma determinista (`demo/domain/generator.py`): patrón semanal, quincena, picos de empanada que
  suben la gaseosa al día siguiente. Varios productos quedan bajo el mínimo (alertas al instante); al cargar se
  generan alertas y se recalcula la co-ocurrencia en segundo plano.
- DELETE borra todo lo que cuelga de los productos de ejemplo (alertas, recomendaciones, predicciones,
  co-ocurrencias, **todas sus ventas, también las manuales**, movimientos y productos). Las categorías y
  proveedores de ejemplo quedan (sin productos).

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
| RF-15 alertas y marcado de revisadas | ✅ | módulo `alerts` + trabajo diario (`jobs`) |
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
| `MAIL_BACKEND` / `BREVO_API_KEY` / `MAIL_FROM` | **Pendiente**: `brevo`, la API key y el remitente verificado (sin esto los correos solo van al log) |
| `FRONTEND_URL` | **Pendiente**: URL del frontend en Vercel (si no, los enlaces de invitación y del correo-resumen apuntan a localhost) |
| `ENVIRONMENT` | `production` (según el autor, ya configurada; con ella `JWT_SECRET` y `CRON_SECRET` son obligatorias) |
| `CRON_SECRET` | **Pendiente, bloqueante**: valor aleatorio ≥ 32 caracteres, el mismo que el secret de GitHub. **Crearla antes de desplegar la fase 5** o la app no arranca |

**Secrets de GitHub Actions** (repo → *Settings → Secrets and variables → Actions*), para
`.github/workflows/daily-jobs.yml`:

| Secret | Valor |
|---|---|
| `CANTINAPP_API_URL` | `https://cantinapp.onrender.com` (sin barra final) |
| `CRON_SECRET` | El mismo valor que `CRON_SECRET` en Render |

Generar el secreto, por ejemplo: `python -c "import secrets; print(secrets.token_urlsafe(48))"`.
GitHub puede pausar los workflows programados de un repo sin actividad en 60 días (se reactivan desde la
pestaña *Actions*).

**Verificación del despliegue:** el log muestra `Application startup complete`
y `Your service is live`. El `SELECT 1` del lifespan tiene límite de 15 s y **ya no
bloquea el arranque** (Render mataba el servicio si no veía el puerto): si la BD no
responde, solo deja un error en el log, así que confirma la conexión con `/health/db`.
Las conexiones nuevas a asyncpg tienen `timeout` de 10 s. Comprobar con:
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
- `JWT_SECRET` (≥ 32 caracteres) y `ENVIRONMENT=production` en Render: según el autor ya están
  configuradas (no verificado desde aquí). Fuera de `development` la app no arranca con el secreto por
  defecto ni sin `CRON_SECRET`.
- **Restringir `CORS_ORIGINS`** al origen real del frontend (el valor por
  defecto `["*"]` permite cualquier origen). `allow_credentials` está en
  `False`, coherente con autenticación por header Bearer.
- `/health/db` ya no expone detalles (solo `ok` / 503).
- Al equipo se entra por invitación (`/api/business/invitations`, desde 004). Invitar sigue revelando
  si ese correo tiene cuenta (404 si no la tiene); solo dueño/admin pueden hacerlo.
- Las plantillas CSV (`/import/template`) son públicas a propósito: son archivos fijos sin datos de negocios.

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
  la genera sola, las alertas las crea `POST /api/alerts/generate` o el trabajo diario.
- Sin historial, el dueño puede cargar datos de ejemplo (`POST /api/demo`).
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

---

## 11. Frontend (estado y decisiones)

SPA construida sobre la API desplegada. Vive en `frontend/` y **no modifica la API**.

### 11.1 Stack

| Capa | Tecnología |
|---|---|
| Framework | React 19 + Vite 8 (`@vitejs/plugin-react`) |
| Rutas | React Router 7 (`react-router-dom`) |
| UI | Material UI 9 (`@mui/material`, `@mui/icons-material`) + `@mui/x-charts` (gráficas) |
| Estilos | Tailwind CSS v4 (`@tailwindcss/vite`) + Emotion (base de MUI) |
| Lint | ESLint 10 (`eslint-plugin-react-hooks`, `eslint-plugin-react-refresh`) |

```
frontend/
  src/
    api/        client.js (fetch + Bearer + 401), helper.js (un método por recurso)
    auth/       context.js, ProtectedRoute.jsx   (AuthProvider vive en App.jsx)
    components/ layout/{AppLayout,BusinessDialog,OnboardingDialog}.jsx
                auth/{AuthShell,LegalDialog}.jsx
                ui/{States,Stamp,PageHeader,Section,StatCard,DataTable,FormDialog,CsvImportDialog,
                    DemoData,Logo,IconField,SearchField,SelectField}.jsx
    hooks/      useApi.js, useDebounced.js, usePagination.js, useProductOptions.js
    pages/      Login, Register, Dashboard, Products, Inventory, Sales, Analytics,
                Replenishment, Alerts, Profile, NotFound
    theme/      color-mode.js (claro/oscuro)
    theme.js    tema MUI (refleja los tokens)
    index.css   ÚNICA hoja de estilos (tokens + clases de superficie)
  .env / .env.example   VITE_API_URL
```

### 11.2 Arranque y configuración

```powershell
# desde frontend/
npm install
npm run dev      # http://localhost:5173
npm run lint
npm run build
```

- `VITE_API_URL=https://cantinapp.onrender.com` (nunca fija en el código).
- Auth: JWT en `Authorization: Bearer`; token en `cantinapp.token` y la sesión completa
  (`SessionOut`) en `cantinapp.session` (`localStorage`). Al arrancar se refresca con
  `GET /auth/me`. Un `401` limpia la sesión y redirige a `/login` (evento
  `cantinapp:unauthorized`). Cambiar de negocio guarda el token nuevo y remonta las páginas
  (`<Outlet key={business_id}>`).
- Cold start de Render: `States.Loading` avisa "El servidor está despertando…"
  tras 5 s; no se trata como error con un timeout corto.
- Nunca se envía `business_id`: lo deduce el backend del token.

### 11.3 Rutas

| Ruta | Pantalla | Endpoints |
|---|---|---|
| `/login`, `/registro` | Acceso | `POST /api/auth/{register,login,logout}`, `GET /api/auth/me` |
| `/` | Dashboard + datos de ejemplo | `GET /api/dashboard`, `/api/demo` |
| `/productos` | Productos + CSV | `/api/products`, `POST /api/products/import`, `GET /api/products/import/template` |
| `/inventario` | Inventario + movimientos | `/api/inventory`, `POST /api/inventory/movements` |
| `/ventas` | Venta manual + import CSV | `/api/sales`, `POST /api/sales/import`, `GET /api/sales/import/template`, `GET /api/demo` (aviso) |
| `/analisis` | Analítica | `GET /api/analytics/{sales,top-products}` |
| `/reabastecimiento` | Predicción + recomendación + acierto + co-ocurrencia + datos de ejemplo | `POST /api/forecasting`, `GET /api/forecasting/accuracy`, `/api/recommendations`, `GET /api/recommendations/cooccurrence`, `POST .../cooccurrence/recompute`, `/api/demo` |
| `/alertas` | Alertas | `/api/alerts`, `/generate`, `PATCH /{id}/review` |
| `/compuestos` | Recetas de productos compuestos (solo en el menú si `session.composites_enabled`) | `GET /api/products/composites`, `PUT /api/products/{id}/components` |
| `/perfil?tab=yo\|negocio\|sedes\|equipo` | Perfil del usuario, del negocio, sedes y equipo | `/api/auth/{me,password}`, `/api/business/*` |

- **Registro:** casillas de Términos y de Política de privacidad y cookies (obligatorias) y de
  uso anónimo para ML (opcional); cada enlace abre `LegalDialog`. Sin «tu nombre»: se pide en el
  perfil. Tarjeta ancha (`AuthShell wide`) para caber sin scroll en ~650 px de alto.
- **Tras registrarse:** `OnboardingDialog` con flecha rizada hacia el bloque «Negocio» de la
  barra lateral (en móvil, al botón de menú). Ese bloque dice «Completa tu perfil →» y, con el
  perfil completo, muestra el nombre del negocio.
- **Selector de negocio** arriba del menú (en móvil, en el header): cambiar o crear negocio. Si al
  iniciar sesión hay más de uno, se abre para elegir. Sin negocio activo, la página lo pide.
- Productos: "Desactivar" = borrado lógico; **editar no cambia stock**.
- Inventario: el stock solo cambia por movimientos (PURCHASE > 0, ADJUSTMENT ≠ 0).
- Ventas: `422` por stock insuficiente se muestra en contexto; el CSV lleva
  `affects_inventory` (por defecto apagado) y muestra errores por fila.
- **CsvImportDialog** (ventas y productos): botón «Descargar plantilla» (`templateUrl`), resumen con
  «N omitidas porque ya estaban cargadas» y, ante un 409, aviso con «Importar de todos modos»
  (`confirm_reimport=true`). `upload(file, { confirmReimport })`.
- Reabastecimiento: un `422` (< 30 días de historial) muestra un estado explicativo
  con enlace a `/ventas` y el botón de datos de ejemplo. Selector de modelo con «Automático
  (recomendado)» por defecto; muestra el modelo elegido y el error del backtest en unidades por día.
  Tarjeta «Qué tan acertadas han sido las predicciones» (vacía y explicada si aún no hay periodos cumplidos).
- **DemoData** (`components/ui/DemoData.jsx`): con datos de ejemplo muestra el aviso y «Borrar datos de
  ejemplo» (solo dueño); en un negocio vacío y para el dueño, «Cargar datos de ejemplo». Con `noticeOnly`
  (diálogo de CSV de ventas) nunca ofrece cargar.
- `GET /api/dashboard` **no** devuelve predicción (brecha de HU08): el Dashboard
  enlaza a `/reabastecimiento`.

### 11.4 Sistema de diseño

- Mundo visual **«boceto a mano / naive»** (desde 2026-10-31; reemplaza a «Kraft y
  sello»). Referencias: `cantinapp-login.html` y `cantinapp-dashboard.html` en la raíz
  (no versionadas).
  - Claro: fondo `#fdfbf7`, tinta `#1c1917`, acento `#f97316` (hover `#ea580c`),
    acento suave `#ffedd5`.
  - Oscuro: «pizarra con tiza»: fondo `#1a1612`, bordes crema `#d6cdbf`, acento
    `#fb923c`.
  - Bordes de 2 px con radios irregulares (`--radius-sketch`, `-alt`, `-sm`); al pasar
    el ratón cambia el radio y aparece una sombra desplazada.
- **Accesibilidad:** el texto sobre botones naranjas es tinta oscura (el blanco sobre
  `#f97316` da 2,8:1). El naranja como texto sobre claro usa `--brand-ink` `#c2410c`.
- Claro y oscuro (sistema + `data-theme`), con conmutador en la barra lateral.
- Tipografía: **Comic Neue** (h1–h3, `font-display`) + **Inter** (texto y cifras con
  `tabular-nums`; `font-mono` apunta a Inter).
- Logo: `public/logo.webp` (192 px, 9 KB) y `public/favicon.png`, generados desde
  `DarioGomez.png` (1,4 MB, no versionado).
- Componentes base: `Section` (bloque con título y acciones), `Logo`,
  `IconField` / `PasswordField` (campo con icono y botón para ver la contraseña),
  `StatCard` (KPI con `surface-lift`).
- Fuente de verdad de tokens: `src/index.css` (`@theme` + variables `:root` /
  `data-theme`); `src/theme.js` solo refleja lo que MUI necesita.
- Layout con Tailwind y componentes complejos con MUI. Clases de superficie
  reutilizables (`.surface`, `.surface-inset`, `.filter-row`) en `index.css`. Sin
  CSS por componente ni por pantalla.

### 11.5 Integración MUI + Tailwind v4 (causa raíz de defectos)

MUI y Tailwind v4 compiten por el orden de capas CSS. Patrón correcto en Vite:

1. `src/index.css`: declarar `@layer theme, base, mui, components, utilities;`
   **antes** de `@import "tailwindcss";`.
2. `src/App.jsx`: `<StyledEngineProvider enableCssLayer>` con
   `<GlobalStyles styles="@layer theme, base, mui, components, utilities;" />` como
   **primer hijo**.

Sin el `GlobalStyles`, Emotion inyecta `@layer mui {}` antes de que se fije el orden
y el preflight de Tailwind termina pisando a MUI: etiquetas flotantes montadas sobre
el texto, botones sin fondo ni relleno, inputs sin borde y checkbox con el azul del
navegador. **No** usar `CssBaseline`: el reset base lo aporta el preflight de Tailwind.

### 11.6 Controles unificados (`theme.js`)

- Un solo aspecto para TextField, Select, Checkbox, Switch, Button (contained /
  outlined / text), IconButton, ToggleButton y Tabs: altura mínima ~44 px, radio
  único, borde sutil, anillo de foco del color primario y estados hover / disabled /
  error. El texto de ayuda va siempre **debajo** del campo.
- Tablas con filas cómodas y cabecera discreta; jerarquía por tamaño y peso moderado.
- `States.jsx`: **skeleton loaders con la forma del contenido** (`Loading variant=
  table|dashboard|chart|list|form|page`), `PageSkeleton` (fallback del `Suspense` de las páginas,
  **dentro** de `AppLayout` para que la barra no desaparezca) y `AppShellSkeleton` (mientras se
  verifica la sesión). Estados vacío y error con icono, título y acción.

### 11.6.1 Responsive (móvil, verificado a 375 px)

- `AppLayout`: **columna en móvil** (`flex-col md:flex-row`); antes el header móvil quedaba como
  columna a la izquierda y aplastaba el contenido.
- Tablas: `hideOnMobile` en columnas secundarias y `RowActions` (iconos en ≥ sm, menú «⋮» en
  móvil). Inventario muestra el estado bajo el nombre; Ventas, la cantidad.
- `.filter-row`: de a dos por fila en móvil (`flex: 1 1 10rem`). KPIs del dashboard en 2×2.
- `theme.js`: diálogos con 16 px de margen en móvil, celdas más compactas y botones de icono de
  44 px con `pointer: coarse`.

### 11.7 Verificación

- `npm run lint` y `npm run build` en verde; rutas con carga diferida (`React.lazy`).
- El contrato de la API se verificó contra
  `https://cantinapp.onrender.com/openapi.json` (campos y parámetros coinciden).
- Regla ESLint `react-hooks/set-state-in-effect` desactivada en `eslint.config.js`:
  los hooks de carga y el arranque de sesión usan `setState` dentro de un efecto de
  forma intencional.
- Rama `feature/juan.ruiz/FrontendV0.1`; commit "Frontend MVP v0.1: SPA React + Vite
  + MUI sobre la API desplegada…". El PR lo abre el autor.

### 11.8 Pendientes

- **CORS en Render:** añadir el origen del frontend a `CORS_ORIGINS` (es la causa más
  probable de que las peticiones fallen en local).
- Probar en un teléfono real: drawer abierto, menús «⋮», modales y la flecha de bienvenida
  (las capturas automáticas no permiten clics). Teclado y foco, contraste en modo oscuro.
- `DESIGN.md` describe el estilo anterior («Kraft y sello»): está **obsoleto** tras el
  rediseño de 2026-10-31.
- El Dashboard no recibe predicción del backend (ver 11.3).
- Probar en navegador las pantallas de la rama `PrediccionAlertasCSV` (diálogos de CSV, acierto,
  datos de ejemplo): solo se verificaron con lint y build.

---

## 12. Bitácora de sesiones

### 2026-10-31 — Co-ocurrencia (Fase 1) + rediseño visual

Rama `feature/juan.ruiz/MotorPredictorCo-Ocurrencia`, publicada en GitHub (sale de
`FrontendV0.1`). **El merge a `main` lo hace el autor.**

| Commit | Contenido |
|---|---|
| `ddc4597` | Arranque tolerante a una BD lenta: `timeout` de asyncpg (10 s) y `SELECT 1` del lifespan con límite de 15 s sin bloquear el arranque |
| `2253331` | Motor de co-ocurrencia: dominio puro, repositorios, endpoints, script de cron, migración 001, 6 tests (25 en verde) |
| `660ea87` | Rediseño visual estilo boceto, componentes base y pantalla «Productos que suben después» en Reabastecimiento |

**Despliegue, en este orden:**
1. **BD (pendiente):** ejecutar `db/migrations/001_product_cooccurrences.sql` en Supabase.
2. **Backend:** merge a `main` y Render redespliega solo. Sin dependencias nuevas ni
   variables obligatorias; las `COOCCURRENCE_*` son opcionales.
3. **Frontend:** el mismo merge; Vercel reconstruye solo (`VITE_API_URL` ya configurada).
4. **Opcional:** Render Cron Job (de pago) con
   `python -m scripts.recompute_cooccurrence`, Root Directory `backend`, mismas
   variables `DB_*`. Sin él, se usa el botón **Recalcular**.

**Decisiones del algoritmo** (detalle en la sección 7):
- Días sin ventas = 0.
- Media y desviación de los 14 días previos, sin incluir el día evaluado.
- Con desviación 0, cualquier subida sobre la media cuenta como pico (caso «flores en
  San Valentín»).
- B «sube» si supera su propia media en +1..+3; cuenta una vez por pico de A.
- Score = coincidencias / picos de A; se descartan pares con menos de 3 coincidencias.

**Limitaciones conocidas:**
- No descuenta subidas generales del negocio (quincena, festivos).
- Coste O(productos²): con cientos de productos el recálculo tarda segundos.
- El botón Recalcular recarga a los 4 s sin saber si el cálculo terminó (`shortcut:`
  en `Replenishment.jsx`).

**Verificación hecha:** pytest (25 tests), `npm run lint` y `npm run build` en verde.
Capturas de `/login` en claro y oscuro y de `/registro` en móvil. **No** se probaron en
navegador las pantallas internas (requieren sesión) ni la co-ocurrencia contra la BD real.

### 2026-11-01 / 02 — Registro legal, CSV de productos, multi-negocio, responsive

Rama `feature/juan.ruiz/ProductosCSV&CompleteProfile`. Commit `35d2b6e` (términos y CSV de
productos); **lo demás está sin commit** (multi-negocio, perfil, registro ajustado, responsive,
skeletons).

- **Registro:** confirmación de contraseña; casillas de Términos, Privacidad y cookies (una sola)
  y ML anónimo (opcional); modales legales con las figuras del login. Consentimientos guardados
  en `user_consents` (migración 002) con versión y fecha. Textos legales sin revisión de un
  abogado (`CONTACT` en `LegalDialog.jsx`).
- **CSV:** carga de productos (`POST /api/products/import`). Los dos CSV aceptan `;` (Excel en
  español), Windows-1252, coma decimal y máximo 5 MB; `error_rows` cuenta filas, no errores.
- **Multi-negocio:** migración 003, módulo `business`, endpoints de sesión en auth, selector de
  negocio, bienvenida con flecha, página `/perfil` (sección 6, 7 y 11.3).
- **Responsive y skeletons:** sección 11.6 y 11.6.1.
- **Verificación:** 40 tests de pytest, `npm run lint` y `npm run build` en verde; capturas del
  registro (1366×650, 1280×600) y de las pantallas internas a 375 px con una API falsa local.
  **No** probado contra Supabase ni con el backend nuevo desplegado.
- El login con el **backend anterior** desplegado daba `Cannot read properties of undefined
  (reading 'length')`: el backend viejo no envía `businesses`. Se blindó con `?.`, pero perfil,
  equipo y cambio de negocio necesitan el backend nuevo.

### 2026-11-04 — Correo: recuperar contraseña e invitaciones (rama `feature/juan.ruiz/WebMail`)

- **Envío:** `app/core/mailer.py`. `MAIL_BACKEND=console` (por defecto) solo escribe el correo en
  el log, con el código en development; `brevo` usa la API HTTPS de Brevo porque Render (plan
  gratis) bloquea SMTP. Con Brevo y sin dominio propio basta con verificar un remitente
  (`MAIL_FROM`). Los datos de usuarios que van en el HTML se escapan.
- **Recuperar contraseña:** `/recuperar` (enlace en el login y en Perfil → Cambiar contraseña).
  Código de 6 dígitos, 5 min, un solo uso, 5 intentos, uno nuevo por minuto; al cambiarla se
  inicia sesión. Cambiar o recuperar la contraseña cierra las demás sesiones
  (`password_changed_at` contra el `iat` del JWT) y envía un aviso por correo.
- **Invitaciones:** reemplazan el alta directa (`POST /members` ya no existe). Quien invita ve
  un código de seguridad y se lo dice a la persona por otro medio; la persona abre el enlace del
  correo **con la cuenta de ese correo** y escribe el código (`/invitacion`). Reinvitar anula la
  anterior. Pendientes visibles y anulables en Perfil → Equipo.
- **Verificación:** 46 tests de pytest, `eslint` y `vite build` en verde. **No** probado contra
  Supabase ni con Brevo real.

### 2026-11-08 — Predicción, alertas y CSV (rama `feature/juan.ruiz/PrediccionAlertasCSV`)

Sale de `main` en `ebe5d76`. Un commit por fase; **el merge y el PR los hace el autor.**

| Commit | Fase |
|---|---|
| `de5aa72` | 1. CSV de ventas sin duplicados: huella de archivo (409 + `confirm_reimport`) y de fila (`skip_duplicates`), `duplicate_rows`, migración 005 con backfill |
| `bddcd6b` | 2. Plantillas CSV públicas de ventas y productos + botón «Descargar plantilla» |
| `065bafb` | 3. `SEASONAL_WEEKLY`, `AUTO` por defecto (backtest 14 días, WAPE/MAE), confianza = 1 − WAPE, migración 006 |
| `0ab9b87` | 4. `GET /api/forecasting/accuracy` y tarjeta de acierto en Reabastecimiento |
| `4adeea3` | 5. Trabajo diario (`POST /api/internal/jobs/daily`, script, GitHub Actions), resolución automática de alertas, correo-resumen, migración 007 |
| `9f58b56` | 6. Datos de ejemplo (`/api/demo`), migración 008 |
| `c719565` | 7. `docs/propuesta-inventario-por-sede.md` (**solo propuesta**) |

**Decisiones:**
- Plantillas públicas (sin token): archivos fijos, sin datos de negocios. Confirmado por el autor.
- El backfill de huellas numera las repeticiones por negocio, no por archivo (las copias ya duplicadas no
  chocan con el índice único).
- Estacional por factores de día de la semana en vez de Holt-Winters (sección 7).
- El trabajo diario no regenera predicciones; «un correo al día» se mide en días UTC.
- Resolución automática de alertas = `REVIEWED` con `reviewed_by` NULL (sin migración).
- Datos de ejemplo solo en negocios sin ventas y sin tocar el stock (`affects_inventory=false`).
- Los tests del endpoint interno llaman la función directamente: `TestClient` exige `httpx`, que no está
  en las dependencias y no se agregó.

**Verificación hecha:** 73 tests de pytest (eran 46), `npm run lint` y `npm run build` en verde al cerrar
cada fase. El esquema OpenAPI incluye las rutas nuevas y oculta la interna.
**No verificado:** nada se ejecutó contra Supabase ni contra el backend desplegado: migraciones 005–008
(en especial el backfill de la 005 y los nombres por defecto de los CHECK que se reemplazan), el `INSERT`
masivo de ventas de ejemplo, el borrado en cascada de `/api/demo`, el envío real por Brevo, ni el workflow
de GitHub Actions. Tampoco se probaron las pantallas en un navegador.

### 2026-11-11 — Lista de tareas: roles, sedes, registro de invitados, buscador de productos (sin commit)

Sale de `main` en `2bd840b`. Todo en el árbol de trabajo, **sin commit**.

| # | Tarea | Cambio |
|---|---|---|
| 1 | Reactivar productos | `ProductUpdate.is_active`; acción «Activar» en Productos |
| 2 | Cuenta para quien será invitado | `/register` con `business_name` opcional; enlace «¿Te invitaron a un negocio? Crea solo tu cuenta» en Registro; si llega desde `/invitacion` entra en ese modo y vuelve a la invitación. Login → Registro conserva el destino |
| 3 | Bloque «Completa tu perfil» poco visible | Ícono `ManageAccounts`, fondo `bg-brand-tint` y texto más oscuro mientras el perfil está incompleto (`AppLayout.jsx`) |
| 4 | Modal para buscar productos | `components/ui/ProductPicker.jsx`: búsqueda, categoría, orden y paginación en servidor; reemplaza los selects de producto en Ventas (filtro y registrar venta) y Análisis |
| 5 | Admin no edita el negocio | `_require_owner` en perfil, sedes y autorización ML; `isOwner` en el contexto de auth; el admin sigue invitando |
| 6 | Ventas por sede | Migración 009; `CurrentUser.location_id` + `scoped_location`; filtro en ventas, análisis (3 rutas) y dashboard; `components/ui/LocationFilter.jsx` + `hooks/useLocationScope.js` (con sede asignada muestra un sello en vez del selector); columna «Sede» en Ventas para quien ve todas; sede (por defecto la principal) al registrar venta y al cargar CSV |
| 7 | Asignar sede al empleado | Sede en la invitación (se aplica al aceptar) y selector de sede por persona en Equipo; `businessApi.changeRole` → `updateMember(userId, role, locationId)` |

**Decisiones:**
- Sede NULL = «todas las sedes» (compatibilidad con miembros y ventas anteriores). El dueño siempre ve todas.
- El inventario **no** se dividió por sede (lo eligió el autor); la propuesta de `docs/propuesta-inventario-por-sede.md` sigue abierta.
- No se borra una sede con ventas o personas asignadas (409) para no ampliar sin querer lo que ve un empleado.
- La autorización de datos ML pasó también a solo-dueño (es dato del negocio).
- Las categorías del buscador salen de los primeros 200 productos (`shortcut:` en `ProductPicker.jsx`).

**Verificación hecha:** 88 tests de pytest (3 nuevos: permisos de dueño, reglas por sede, registro sin
negocio), `import app.main`, `npx eslint src` y `npx vite build` en verde.
**No verificado:** la migración 009 y las consultas SQL nuevas contra Postgres (los tests usan repositorios
falsos) y las pantallas en el navegador. El autor dijo que lo verifica él.
**Ojo:** durante la sesión el editor reformateó (Prettier) `BusinessDialog.jsx`, `OnboardingDialog.jsx` y
`package-lock.json`; no son cambios de esta tarea, revisar antes del commit.

### 2026-11-11 (tarde) — Productos compuestos (rama `feature/juan.ruiz/CrearUniones/Compuetos`, sin commit)

Pedido: una sección «Compuestos» que se activa desde Perfil → Negocio, para que un restaurante maneje el
stock de cocina con recetas (una hamburguesa lleva pan, carne...).

| Capa | Cambio |
|---|---|
| BD | Migración `010_compuestos.sql` (ver sección 4), aplicada también en `schema.sql`; `product_components` añadida al `TRUNCATE` de `reset_datos.sql` |
| Negocio | `composites_enabled` en `PROFILE_FIELDS`, `BusinessProfile`, `BusinessRecord`, `BusinessUpdate`/`BusinessOut`; se cambia con `PUT /api/business` (solo dueño) |
| Sesión | `composites_enabled` en `Membership`, `Session`, `SessionOut` y `_session_out`: el menú lo lee de la sesión |
| Productos | Repositorio: `composites_enabled`, `has_recipe`, `list_composites`, `with_recipe`, `used_as_component`, `set_components`; handler `set_recipe` con las validaciones; endpoints `GET /composites` y `PUT /{id}/components` |
| Ventas | `register_sale` no exige stock propio a un compuesto (lo valida el trigger) |
| Frontend | `pages/Composites.jsx` (tabla con receta y «Se pueden armar», diálogo de receta con `ProductPickerField` por componente, quitar receta; si está apagada muestra cómo activarla); ruta `/compuestos`; ítem «Compuestos» (`LunchDiningOutlined`) en `AppLayout` filtrado por `compositesEnabled`; `CompositesSection` en Perfil → Negocio (interruptor, llama a `refresh()`); `productsApi.composites` / `setRecipe`; `compositesEnabled` en el contexto de auth |
| Tests | `tests/test_composites.py`: reglas de la receta y venta manual de un compuesto sin stock propio |

**Decisiones:**
- Activar la sección es **solo del dueño** (coherente con «solo el dueño edita el negocio»). El autor pidió
  «el administrador»: si se quiere admin, endpoint aparte con `_require_admin`. **Pendiente de confirmar.**
- Un producto es compuesto si tiene filas en `product_components`; no hay columna `is_composite`.
- Con la sección apagada las recetas se conservan pero se ignoran (trigger, vista y venta manual).
- Cantidades enteras, igual que el stock: ingredientes por peso se manejan en gramos.
- `shortcut:` en `fn_sale_restore_inventory`: al borrar una venta se devuelve según la receta **vigente**, no
  la del momento de la venta.

**Verificación hecha:** 90 tests de pytest (2 nuevos), `npx eslint` de los archivos tocados y `vite build`
en verde. El `venv` del repo apunta a un Python de otra máquina: se usó un venv temporal con Python 3.12.
**No verificado:** la migración 010, los triggers y las consultas SQL nuevas contra Postgres; las pantallas en
el navegador.
**Limitaciones conocidas:** predicción y reabastecimiento siguen viendo la venta del compuesto, no proyectan
consumo de componentes; en Ventas, «Stock disponible» de un compuesto muestra 0 (`ProductOut` lee
`products.stock_quantity`, no la vista).

### Próxima sesión — pendientes

1. **Desplegar en orden:**
   1. Supabase: migraciones `001` → … → `008` (reportadas como ejecutadas el 2026-11-08), **`009`** y **`010`**.
   2. Render: `CRON_SECRET` (≥ 32, **antes** del deploy), variables de correo y `FRONTEND_URL`.
   3. GitHub: secrets `CANTINAPP_API_URL` y `CRON_SECRET`.
   4. Merge a `main` (Render + Vercel). Ejecutar el workflow «Trabajo diario» a mano (*Run workflow*) y
      revisar su salida y el log de Render.
   5. Validar con datos reales: registro, login, cambio de negocio, perfil, CSV repetido (409 y omitidas),
      predicción AUTO, datos de ejemplo (cargar y borrar) y co-ocurrencia.
2. Probar en un teléfono real (ver 11.8).
3. Decidir sobre `docs/propuesta-inventario-por-sede.md` (sección 7 de ese documento: decisiones abiertas).
4. Posibles siguientes pasos: verificar el correo al registrarse, invitar a quien aún no tiene cuenta (hoy
   debe registrarse primero con «¿Te invitaron?»), endpoint de categorías para el buscador, sede en la
   vista previa de la invitación y en invitaciones pendientes,
   transferir el negocio a otro dueño, mostrar en Alertas cuáles se resolvieron solas.
   Compuestos: confirmar si el admin también puede activarlos; mostrar en Ventas el stock armable;
   proyectar consumo de componentes en reabastecimiento.
5. Decidir si se borra `frontend/public/DarioGomez.png` y actualizar o retirar `DESIGN.md`.
6. Sigue abierto: `CORS_ORIGINS` en Render.
