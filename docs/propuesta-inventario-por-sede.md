# Propuesta: inventario por sede

Estado: **propuesta, no implementada.** La decisión de construirla es del autor.
Fecha: 2026-11-08 · Rama de referencia: `feature/juan.ruiz/PrediccionAlertasCSV`.

## 1. Problema

Hoy las sedes (`business_locations`, migración 003) son solo datos de perfil. El stock vive en
`products.stock_quantity`, una sola cifra por producto para todo el negocio. Un dueño con dos
tiendas no sabe en cuál se está acabando un producto, ni puede pasar mercancía de una a otra.

## 2. Diseño propuesto

**Idea central:** el catálogo (nombre, precio, categoría, proveedor) sigue siendo del negocio; lo
que pasa a ser por sede es la existencia. Se agrega una tabla de stock por (producto, sede) y
`products.stock_quantity` se mantiene como **suma** de las sedes (caché), para no romper a quien
hoy la lee (dashboard, recomendación, alertas, frontend).

### 2.1 Esquema

```sql
-- Stock por sede (caché, igual que hoy products.stock_quantity: solo lo cambian los movimientos)
CREATE TABLE product_stock (
    business_id     uuid    NOT NULL REFERENCES businesses (id),
    product_id      uuid    NOT NULL,
    location_id     uuid    NOT NULL,
    stock_quantity  integer NOT NULL DEFAULT 0 CHECK (stock_quantity >= 0),
    min_stock       integer,          -- NULL = usa products.min_stock
    PRIMARY KEY (business_id, product_id, location_id),
    FOREIGN KEY (business_id, product_id)  REFERENCES products (business_id, id),
    FOREIGN KEY (business_id, location_id) REFERENCES business_locations (business_id, id)
);
-- + RLS activado sin políticas + REVOKE a anon/authenticated, como el resto.

ALTER TABLE inventory_movements ADD COLUMN location_id uuid;   -- NOT NULL tras el backfill
ALTER TABLE inventory_movements ADD FOREIGN KEY (business_id, location_id)
    REFERENCES business_locations (business_id, id);
ALTER TABLE inventory_movements DROP CONSTRAINT movement_sign_matches_type;  -- se amplía con TRANSFER
ALTER TABLE inventory_movements ADD COLUMN transfer_id uuid;   -- agrupa la salida y la entrada

ALTER TABLE sales ADD COLUMN location_id uuid;                 -- NULL permitido en ventas CSV históricas
ALTER TABLE sales ADD FOREIGN KEY (business_id, location_id)
    REFERENCES business_locations (business_id, id);
```

- **Transferencias:** `movement_type = 'TRANSFER'` con dos filas (−n en la sede origen y +n en la
  destino) unidas por `transfer_id`, dentro de una sola transacción.
- **Trigger `fn_apply_inventory_movement`:** actualiza `product_stock` de la sede (con bloqueo de
  fila, como hoy) y luego `products.stock_quantity` (suma). Un `CHECK` de stock no negativo por
  sede reemplaza al actual a nivel de producto.
- **Trigger de venta:** descuenta en la sede de la venta; si `location_id` es NULL (CSV histórico
  con `affects_inventory=false`) no toca stock, igual que hoy.
- **Borrar una sede** que tiene stock o movimientos: se bloquea (FK) o se pide transferir antes.

### 2.2 Vistas

- `v_inventory` se mantiene igual (negocio completo, sobre la suma).
- Nueva `v_inventory_by_location` con el mismo `CASE` de estado (AGOTADO / BAJO / NORMAL) por
  (producto, sede), usando `coalesce(ps.min_stock, p.min_stock)`.
- `v_daily_sales` agrega `location_id` como columna de agrupación opcional (o se crea
  `v_daily_sales_by_location`), para no cambiar las consultas actuales.

## 3. Migración de datos existentes

1. Todo negocio sin sedes recibe una sede **«Principal»** (`is_main = true`).
2. `INSERT INTO product_stock` con todo el stock actual en la sede principal.
3. Backfill de `inventory_movements.location_id` y `sales.location_id` (solo las que afectaron
   inventario) con la sede principal; luego `location_id` pasa a `NOT NULL` en movimientos.
4. Verificación dentro de la misma migración: para cada producto,
   `sum(product_stock) = products.stock_quantity`; si no cuadra, `RAISE EXCEPTION` (aborta todo).

Es idempotente si cada paso usa `ON CONFLICT DO NOTHING` / `WHERE location_id IS NULL`.

## 4. Impacto por módulo

| Módulo | Cambio |
|---|---|
| `inventory` | Movimientos piden `location_id` (por defecto la principal); endpoint nuevo `POST /api/inventory/transfers`; `GET /api/inventory?location_id=` usa la vista por sede. |
| `sales` | Venta manual con `location_id` (por defecto la principal). CSV: columna opcional `sede`; sin ella, sede principal si `affects_inventory=true`, NULL si es histórico. Entra en la huella de fila de la fase 1 solo si viene en el archivo (para no invalidar las huellas existentes). |
| `products` | Stock inicial se registra en la sede principal (o en la elegida). |
| `business` | No se puede borrar una sede con stock; al crear la primera sede de un negocio que ya tenía stock, se ofrece moverlo. |
| `forecasting` | Sin cambio por defecto (demanda del negocio). Opcional: `location_id` en `ForecastRequest` filtrando la serie; con pocas ventas por sede el backtest será menos confiable y el mínimo de 30 días se alcanza más tarde. |
| `recommendations` | Cantidad sugerida por sede = demanda de la sede × lead time + mínimo de la sede − stock de la sede. Si la predicción es del negocio, repartir por la proporción histórica de ventas de cada sede. |
| `alerts` | La alerta pasa a ser por (producto, sede): columna `location_id` y el índice único parcial cambia a `(business_id, product_id, location_id) WHERE status = 'PENDING'`. El correo-resumen agrupa por sede. |
| `dashboard` | Filtro por sede en KPIs y en «Productos que requieren abastecimiento». |
| `demo` | Los datos de ejemplo se cargan en la sede principal. |
| Frontend | Selector de sede en Inventario, Ventas y Dashboard (con «Todas»); diálogo de transferencia. |

## 5. Riesgos

- **Coherencia de la caché doble** (`product_stock` y `products.stock_quantity`): todo cambio debe
  pasar por el trigger de movimientos. Un `UPDATE` directo a cualquiera de las dos lo rompe.
- **Concurrencia en transferencias:** bloquear las dos filas de `product_stock` siempre en el
  mismo orden (por `location_id`) para evitar deadlocks.
- **CSV histórico sin sede:** la predicción por sede no tendrá esos datos; documentarlo en la UI.
- **Alertas existentes:** al migrar, las pendientes se asignan a la sede principal.

## 6. Esfuerzo estimado

| Bloque | Estimado |
|---|---|
| Migración + triggers + vistas + verificación | 1,5 – 2 días |
| Backend: inventario, transferencias, ventas, productos, sedes | 2 – 3 días |
| Alertas y recomendación por sede | 1 – 1,5 días |
| Frontend: selector de sede, transferencias, filtros | 2 – 3 días |
| Tests (lógica pura de reparto y de estado por sede) y pruebas contra una BD real | 1 – 1,5 días |
| **Total** | **≈ 7,5 – 11 días** de una persona |

Predicción por sede queda fuera de esa cifra (≈ 1 día más) y se recomienda dejarla para después de
tener un mes de ventas con sede.

## 7. Decisiones abiertas para el autor

1. ¿El precio puede variar por sede? (Este diseño asume que no.)
2. ¿Stock mínimo por sede desde el inicio o solo el del producto?
3. ¿Los miembros quedan limitados a ciertas sedes (permisos) o ven todas?
4. ¿La predicción por sede entra en la primera versión?
