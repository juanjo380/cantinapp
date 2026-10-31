-- =============================================================================
-- CantinAPP MVP v0.1 - Modelo relacional (PostgreSQL 15+ / Supabase)
-- Ejecutar en: Supabase Dashboard -> SQL Editor (sobre una BD vacia).
--
-- Decisiones de diseno (resuelven puntos abiertos del analisis):
--  1. Multitenancy: toda tabla de negocio lleva business_id y las FK son
--     COMPUESTAS (business_id, id), asi un producto nunca puede apuntar a una
--     categoria, proveedor o venta de OTRO negocio.
--  2. Stock: products.stock_quantity es un valor cacheado que SOLO cambia
--     mediante inventory_movements (libro de movimientos). Una venta genera un
--     movimiento; las compras/reposiciones y ajustes tambien. Todo es atomico.
--  3. Borrado logico de productos (is_active) para conservar el historial.
--  4. Las ventas historicas (CSV) pueden cargarse con affects_inventory = false
--     para no descontar del stock actual.
--  5. Estado de inventario (NORMAL / BAJO / AGOTADO) calculado en la vista
--     v_inventory, nunca almacenado.
-- =============================================================================

BEGIN;

-- ---------------------------------------------------------------------------
-- Utilidades
-- ---------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION set_updated_at()
RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
    NEW.updated_at := now();
    RETURN NEW;
END;
$$;

-- ---------------------------------------------------------------------------
-- 1. Negocios (tenant) y usuarios  [Modulo Autenticacion]
-- ---------------------------------------------------------------------------
CREATE TABLE businesses (
    id          uuid        PRIMARY KEY DEFAULT gen_random_uuid(),
    name        text        NOT NULL CHECK (length(trim(name)) > 0),
    created_at  timestamptz NOT NULL DEFAULT now(),
    updated_at  timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE users (
    id             uuid        PRIMARY KEY DEFAULT gen_random_uuid(),
    business_id    uuid        NOT NULL REFERENCES businesses (id),
    email          text        NOT NULL,
    password_hash  text        NOT NULL,
    full_name      text,
    role           text        NOT NULL DEFAULT 'ADMIN' CHECK (role IN ('ADMIN')),
    is_active      boolean     NOT NULL DEFAULT true,
    created_at     timestamptz NOT NULL DEFAULT now(),
    updated_at     timestamptz NOT NULL DEFAULT now()
);
-- HU01: email unico (sin distinguir mayusculas)
CREATE UNIQUE INDEX ux_users_email ON users (lower(email));
CREATE INDEX ix_users_business ON users (business_id);

-- ---------------------------------------------------------------------------
-- 2. Catalogos: categorias y proveedores  [Modulo Productos]
-- ---------------------------------------------------------------------------
CREATE TABLE categories (
    id          uuid        PRIMARY KEY DEFAULT gen_random_uuid(),
    business_id uuid        NOT NULL REFERENCES businesses (id),
    name        text        NOT NULL CHECK (length(trim(name)) > 0),
    created_at  timestamptz NOT NULL DEFAULT now(),
    UNIQUE (business_id, id),
    UNIQUE (business_id, name)
);

CREATE TABLE suppliers (
    id            uuid        PRIMARY KEY DEFAULT gen_random_uuid(),
    business_id   uuid        NOT NULL REFERENCES businesses (id),
    name          text        NOT NULL CHECK (length(trim(name)) > 0),
    contact_name  text,
    phone         text,
    email         text,
    created_at    timestamptz NOT NULL DEFAULT now(),
    UNIQUE (business_id, id),
    UNIQUE (business_id, name)
);

-- ---------------------------------------------------------------------------
-- 3. Productos
-- ---------------------------------------------------------------------------
CREATE TABLE products (
    id              uuid          PRIMARY KEY DEFAULT gen_random_uuid(),
    business_id     uuid          NOT NULL REFERENCES businesses (id),
    category_id     uuid,
    supplier_id     uuid,
    name            text          NOT NULL CHECK (length(trim(name)) > 0),
    price           numeric(12,2) NOT NULL CHECK (price >= 0),      -- COP
    stock_quantity  integer       NOT NULL DEFAULT 0,
    min_stock       integer       NOT NULL DEFAULT 0 CHECK (min_stock >= 0),
    lead_time_days  integer       NOT NULL DEFAULT 0 CHECK (lead_time_days >= 0),
    is_active       boolean       NOT NULL DEFAULT true,
    created_at      timestamptz   NOT NULL DEFAULT now(),
    updated_at      timestamptz   NOT NULL DEFAULT now(),
    CONSTRAINT products_stock_nonnegative CHECK (stock_quantity >= 0),
    UNIQUE (business_id, id),
    FOREIGN KEY (business_id, category_id) REFERENCES categories (business_id, id),
    FOREIGN KEY (business_id, supplier_id) REFERENCES suppliers  (business_id, id)
);
-- Nombre unico por negocio entre productos activos (permite reutilizar el nombre
-- de un producto desactivado)
CREATE UNIQUE INDEX ux_products_business_name_active
    ON products (business_id, lower(name)) WHERE is_active;
CREATE INDEX ix_products_business_active ON products (business_id, is_active);

-- ---------------------------------------------------------------------------
-- 4. Ventas  [Modulo Ventas]
-- ---------------------------------------------------------------------------
-- Lotes de carga CSV (HU03: validacion con mensajes de error)
CREATE TABLE sales_imports (
    id             uuid        PRIMARY KEY DEFAULT gen_random_uuid(),
    business_id    uuid        NOT NULL REFERENCES businesses (id),
    file_name      text        NOT NULL,
    total_rows     integer     NOT NULL DEFAULT 0,
    imported_rows  integer     NOT NULL DEFAULT 0,
    error_rows     integer     NOT NULL DEFAULT 0,
    status         text        NOT NULL DEFAULT 'PROCESSING'
                   CHECK (status IN ('PROCESSING', 'COMPLETED', 'FAILED')),
    error_detail   jsonb,                       -- [{row, field, message}, ...]
    created_by     uuid        REFERENCES users (id),
    created_at     timestamptz NOT NULL DEFAULT now(),
    UNIQUE (business_id, id)
);

CREATE TABLE sales (
    id                uuid          PRIMARY KEY DEFAULT gen_random_uuid(),
    business_id       uuid          NOT NULL REFERENCES businesses (id),
    product_id        uuid          NOT NULL,
    sale_date         date          NOT NULL,
    quantity          integer       NOT NULL CHECK (quantity > 0),
    unit_price        numeric(12,2) NOT NULL CHECK (unit_price >= 0),  -- precio al momento de la venta
    total_amount      numeric(14,2) GENERATED ALWAYS AS (quantity * unit_price) STORED,
    source            text          NOT NULL DEFAULT 'MANUAL' CHECK (source IN ('MANUAL', 'CSV')),
    affects_inventory boolean       NOT NULL DEFAULT true,
    import_id         uuid,
    created_by        uuid          REFERENCES users (id),
    created_at        timestamptz   NOT NULL DEFAULT now(),
    UNIQUE (business_id, id),
    FOREIGN KEY (business_id, product_id) REFERENCES products      (business_id, id),
    FOREIGN KEY (business_id, import_id)  REFERENCES sales_imports (business_id, id)
);
-- Indices para analisis historico y prediccion (RNF-05)
CREATE INDEX ix_sales_business_product_date ON sales (business_id, product_id, sale_date);
CREATE INDEX ix_sales_business_date         ON sales (business_id, sale_date);
CREATE INDEX ix_sales_import                ON sales (import_id) WHERE import_id IS NOT NULL;

-- ---------------------------------------------------------------------------
-- 5. Libro de movimientos de inventario  [Modulo Inventario]
-- ---------------------------------------------------------------------------
CREATE TABLE inventory_movements (
    id               bigint      GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    business_id      uuid        NOT NULL REFERENCES businesses (id),
    product_id       uuid        NOT NULL,
    movement_type    text        NOT NULL
                     CHECK (movement_type IN ('INITIAL', 'SALE', 'PURCHASE', 'ADJUSTMENT')),
    quantity_change  integer     NOT NULL CHECK (quantity_change <> 0),
    stock_after      integer     NOT NULL,       -- lo asigna el trigger
    sale_id          uuid        REFERENCES sales (id) ON DELETE SET NULL,
    notes            text,
    created_by       uuid        REFERENCES users (id),
    created_at       timestamptz NOT NULL DEFAULT now(),
    FOREIGN KEY (business_id, product_id) REFERENCES products (business_id, id),
    CONSTRAINT movement_sign_matches_type CHECK (
        (movement_type IN ('INITIAL', 'PURCHASE') AND quantity_change > 0)
        OR (movement_type = 'SALE' AND quantity_change < 0)
        OR  movement_type = 'ADJUSTMENT'
    )
);
CREATE INDEX ix_movements_product_date ON inventory_movements (business_id, product_id, created_at DESC);

-- ---------------------------------------------------------------------------
-- 6. Predicciones, recomendaciones y alertas
-- ---------------------------------------------------------------------------
CREATE TABLE forecasts (                          -- [Modulo Prediccion]
    id                uuid          PRIMARY KEY DEFAULT gen_random_uuid(),
    business_id       uuid          NOT NULL REFERENCES businesses (id),
    product_id        uuid          NOT NULL,
    model_type        text          NOT NULL
                      CHECK (model_type IN ('LINEAR_REGRESSION', 'MOVING_AVERAGE')),
    history_days      integer       NOT NULL CHECK (history_days >= 30),   -- RNF-04
    forecast_days     integer       NOT NULL CHECK (forecast_days BETWEEN 1 AND 365),
    forecast_start    date          NOT NULL,
    predicted_demand  numeric(14,2) NOT NULL CHECK (predicted_demand >= 0),
    confidence        numeric(5,4)  CHECK (confidence BETWEEN 0 AND 1),     -- formula por definir
    daily_prediction  jsonb,                      -- [{date, value}, ...] para la grafica
    created_by        uuid          REFERENCES users (id),
    created_at        timestamptz   NOT NULL DEFAULT now(),
    UNIQUE (business_id, id),
    FOREIGN KEY (business_id, product_id) REFERENCES products (business_id, id)
);
CREATE INDEX ix_forecasts_product_date ON forecasts (business_id, product_id, created_at DESC);

CREATE TABLE recommendations (                    -- [Modulo Recomendacion]
    id                  uuid          PRIMARY KEY DEFAULT gen_random_uuid(),
    business_id         uuid          NOT NULL REFERENCES businesses (id),
    product_id          uuid          NOT NULL,
    forecast_id         uuid,
    current_stock       integer       NOT NULL,
    min_stock           integer       NOT NULL,
    lead_time_days      integer       NOT NULL,
    predicted_demand    numeric(14,2) NOT NULL,
    coverage_days       numeric(10,2),            -- stock actual / demanda diaria estimada
    suggested_quantity  integer       NOT NULL CHECK (suggested_quantity >= 0),
    urgency             text          NOT NULL CHECK (urgency IN ('BAJO', 'MEDIO', 'ALTO')),
    justification       text          NOT NULL,
    created_at          timestamptz   NOT NULL DEFAULT now(),
    UNIQUE (business_id, id),
    FOREIGN KEY (business_id, product_id)  REFERENCES products  (business_id, id),
    FOREIGN KEY (business_id, forecast_id) REFERENCES forecasts (business_id, id)
);
CREATE INDEX ix_recommendations_product_date ON recommendations (business_id, product_id, created_at DESC);

-- Co-ocurrencia temporal de picos (migracion 001)
CREATE TABLE product_cooccurrences (              -- [Modulo Recomendacion]
    business_id        uuid         NOT NULL REFERENCES businesses (id),
    product_id         uuid         NOT NULL,     -- A: producto con el pico
    related_product_id uuid         NOT NULL,     -- B: producto que sube en los dias siguientes
    peaks              integer      NOT NULL CHECK (peaks > 0),
    hits               integer      NOT NULL CHECK (hits > 0),
    score              numeric(5,4) NOT NULL CHECK (score BETWEEN 0 AND 1),   -- hits / peaks
    computed_at        timestamptz  NOT NULL DEFAULT now(),
    PRIMARY KEY (business_id, product_id, related_product_id),
    FOREIGN KEY (business_id, product_id)         REFERENCES products (business_id, id),
    FOREIGN KEY (business_id, related_product_id) REFERENCES products (business_id, id),
    CHECK (product_id <> related_product_id)
);

CREATE TABLE alerts (                             -- [Modulo Alertas]
    id                    uuid          PRIMARY KEY DEFAULT gen_random_uuid(),
    business_id           uuid          NOT NULL REFERENCES businesses (id),
    product_id            uuid          NOT NULL,
    recommendation_id     uuid,
    current_stock         integer       NOT NULL,
    min_stock             integer       NOT NULL,
    estimated_demand      numeric(14,2),
    recommended_quantity  integer,
    status                text          NOT NULL DEFAULT 'PENDING' CHECK (status IN ('PENDING', 'REVIEWED')),
    reviewed_by           uuid          REFERENCES users (id),
    reviewed_at           timestamptz,
    created_at            timestamptz   NOT NULL DEFAULT now(),
    FOREIGN KEY (business_id, product_id)        REFERENCES products        (business_id, id),
    FOREIGN KEY (business_id, recommendation_id) REFERENCES recommendations (business_id, id),
    CONSTRAINT alert_review_consistency CHECK (
        (status = 'PENDING'  AND reviewed_at IS NULL)
        OR (status = 'REVIEWED' AND reviewed_at IS NOT NULL)
    )
);
-- Una sola alerta pendiente por producto
CREATE UNIQUE INDEX ux_alerts_one_pending_per_product
    ON alerts (business_id, product_id) WHERE status = 'PENDING';
CREATE INDEX ix_alerts_business_status ON alerts (business_id, status, created_at DESC);

-- ---------------------------------------------------------------------------
-- 7. Triggers de integridad de inventario
-- ---------------------------------------------------------------------------
-- 7.1 Aplica cada movimiento al stock del producto (atomico, con bloqueo de fila).
--     Si el stock quedara negativo, falla con check_violation
--     (constraint products_stock_nonnegative) -> el backend debe responder 422.
CREATE OR REPLACE FUNCTION fn_apply_inventory_movement()
RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE
    v_stock integer;
BEGIN
    IF NEW.movement_type = 'INITIAL' THEN
        -- El stock inicial ya viene en la fila del producto recien creado
        NEW.stock_after := NEW.quantity_change;
        RETURN NEW;
    END IF;

    UPDATE products
       SET stock_quantity = stock_quantity + NEW.quantity_change
     WHERE id = NEW.product_id
       AND business_id = NEW.business_id
    RETURNING stock_quantity INTO v_stock;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Producto % no encontrado para el negocio %', NEW.product_id, NEW.business_id
            USING ERRCODE = 'foreign_key_violation';
    END IF;

    NEW.stock_after := v_stock;
    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_movements_apply
    BEFORE INSERT ON inventory_movements
    FOR EACH ROW EXECUTE FUNCTION fn_apply_inventory_movement();

-- 7.2 Producto nuevo con stock > 0 -> registra movimiento INITIAL
CREATE OR REPLACE FUNCTION fn_product_initial_stock()
RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
    IF NEW.stock_quantity > 0 THEN
        INSERT INTO inventory_movements (business_id, product_id, movement_type, quantity_change, notes)
        VALUES (NEW.business_id, NEW.id, 'INITIAL', NEW.stock_quantity, 'Stock inicial');
    END IF;
    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_products_initial_stock
    AFTER INSERT ON products
    FOR EACH ROW EXECUTE FUNCTION fn_product_initial_stock();

-- 7.3 Venta -> descuenta inventario (RF-08) cuando affects_inventory = true
CREATE OR REPLACE FUNCTION fn_sale_inventory()
RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
    IF NEW.affects_inventory THEN
        INSERT INTO inventory_movements
            (business_id, product_id, movement_type, quantity_change, sale_id, created_by)
        VALUES
            (NEW.business_id, NEW.product_id, 'SALE', -NEW.quantity, NEW.id, NEW.created_by);
    END IF;
    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_sales_inventory
    AFTER INSERT ON sales
    FOR EACH ROW EXECUTE FUNCTION fn_sale_inventory();

-- 7.4 Venta eliminada -> devuelve el stock
CREATE OR REPLACE FUNCTION fn_sale_restore_inventory()
RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
    IF OLD.affects_inventory THEN
        INSERT INTO inventory_movements
            (business_id, product_id, movement_type, quantity_change, notes)
        VALUES
            (OLD.business_id, OLD.product_id, 'ADJUSTMENT', OLD.quantity, 'Reversion por eliminacion de venta');
    END IF;
    RETURN OLD;
END;
$$;

CREATE TRIGGER trg_sales_restore_inventory
    AFTER DELETE ON sales
    FOR EACH ROW EXECUTE FUNCTION fn_sale_restore_inventory();

-- 7.5 updated_at automatico
CREATE TRIGGER trg_businesses_updated BEFORE UPDATE ON businesses FOR EACH ROW EXECUTE FUNCTION set_updated_at();
CREATE TRIGGER trg_users_updated      BEFORE UPDATE ON users      FOR EACH ROW EXECUTE FUNCTION set_updated_at();
CREATE TRIGGER trg_products_updated   BEFORE UPDATE ON products   FOR EACH ROW EXECUTE FUNCTION set_updated_at();

-- ---------------------------------------------------------------------------
-- 8. Vistas de lectura
-- ---------------------------------------------------------------------------
-- HU04: inventario con estado NORMAL / BAJO / AGOTADO
CREATE VIEW v_inventory WITH (security_invoker = true) AS
SELECT
    p.id            AS product_id,
    p.business_id,
    p.name,
    c.name          AS category,
    s.name          AS supplier,
    p.price,
    p.stock_quantity,
    p.min_stock,
    p.lead_time_days,
    CASE
        WHEN p.stock_quantity = 0            THEN 'AGOTADO'
        WHEN p.stock_quantity < p.min_stock  THEN 'BAJO'
        ELSE 'NORMAL'
    END             AS status
FROM products p
LEFT JOIN categories c ON c.id = p.category_id
LEFT JOIN suppliers  s ON s.id = p.supplier_id
WHERE p.is_active;

-- HU05: ventas agregadas por dia (base para mensual/anual, tendencias y prediccion)
CREATE VIEW v_daily_sales WITH (security_invoker = true) AS
SELECT
    business_id,
    product_id,
    sale_date,
    SUM(quantity)     AS units_sold,
    SUM(total_amount) AS revenue
FROM sales
GROUP BY business_id, product_id, sale_date;

-- ---------------------------------------------------------------------------
-- 9. Seguridad en Supabase
-- ---------------------------------------------------------------------------
-- Supabase expone el esquema public por su API REST (PostgREST). Como el acceso
-- a datos lo hace SOLO el backend FastAPI (conexion directa con el rol postgres,
-- que ignora RLS), activamos RLS sin politicas y revocamos permisos a los roles
-- publicos: la API REST de Supabase no podra leer ni escribir nada.
DO $$
DECLARE
    t text;
BEGIN
    FOR t IN SELECT tablename FROM pg_tables WHERE schemaname = 'public' LOOP
        EXECUTE format('ALTER TABLE public.%I ENABLE ROW LEVEL SECURITY', t);
    END LOOP;

    IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'anon') THEN
        REVOKE ALL ON ALL TABLES IN SCHEMA public FROM anon;
    END IF;
    IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'authenticated') THEN
        REVOKE ALL ON ALL TABLES IN SCHEMA public FROM authenticated;
    END IF;
END;
$$;

COMMIT;