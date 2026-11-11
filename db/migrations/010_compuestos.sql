-- =============================================================================
-- 010 - Productos compuestos (recetas): vender una hamburguesa descuenta pan, carne...
-- Ejecutar en: Supabase Dashboard -> SQL Editor, DESPUES de 001-009.
-- Debe ejecutarse ANTES de desplegar el backend que la usa.
-- =============================================================================
BEGIN;

-- 1. Interruptor por negocio (Perfil -> Negocio). Apagado: las recetas se ignoran.
ALTER TABLE businesses ADD COLUMN composites_enabled boolean NOT NULL DEFAULT false;

-- 2. Receta: cuántas unidades de cada componente lleva una unidad del compuesto.
--    Un solo nivel: el backend impide que un componente tenga receta propia.
CREATE TABLE product_components (
    business_id   uuid    NOT NULL,
    product_id    uuid    NOT NULL,
    component_id  uuid    NOT NULL,
    quantity      integer NOT NULL CHECK (quantity > 0),
    PRIMARY KEY (product_id, component_id),
    CHECK (product_id <> component_id),
    FOREIGN KEY (business_id, product_id)   REFERENCES products (business_id, id) ON DELETE CASCADE,
    FOREIGN KEY (business_id, component_id) REFERENCES products (business_id, id) ON DELETE CASCADE
);
CREATE INDEX ix_product_components_component ON product_components (component_id);
-- Solo el backend accede (ver seccion 9 de schema.sql)
ALTER TABLE product_components ENABLE ROW LEVEL SECURITY;
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'anon') THEN
        REVOKE ALL ON product_components FROM anon;
    END IF;
    IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'authenticated') THEN
        REVOKE ALL ON product_components FROM authenticated;
    END IF;
END;
$$;

-- 3. Venta: si el producto tiene receta (y el negocio la activó) descuenta los componentes;
--    si no, el producto mismo. El CHECK de stock no negativo sigue protegiendo cada componente.
CREATE OR REPLACE FUNCTION fn_sale_inventory()
RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
    IF NOT NEW.affects_inventory THEN
        RETURN NEW;
    END IF;
    INSERT INTO inventory_movements
        (business_id, product_id, movement_type, quantity_change, sale_id, created_by, notes)
    SELECT NEW.business_id, pc.component_id, 'SALE', -NEW.quantity * pc.quantity, NEW.id, NEW.created_by,
           'Componente de producto compuesto'
      FROM product_components pc
      JOIN businesses b ON b.id = pc.business_id AND b.composites_enabled
     WHERE pc.business_id = NEW.business_id AND pc.product_id = NEW.product_id;
    IF NOT FOUND THEN
        INSERT INTO inventory_movements
            (business_id, product_id, movement_type, quantity_change, sale_id, created_by)
        VALUES
            (NEW.business_id, NEW.product_id, 'SALE', -NEW.quantity, NEW.id, NEW.created_by);
    END IF;
    RETURN NEW;
END;
$$;

-- 4. Venta eliminada: devuelve el stock por la misma vía.
--    shortcut: usa la receta vigente, no la del momento de la venta; guardar el detalle por venta si se editan recetas a menudo.
CREATE OR REPLACE FUNCTION fn_sale_restore_inventory()
RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
    IF NOT OLD.affects_inventory THEN
        RETURN OLD;
    END IF;
    INSERT INTO inventory_movements (business_id, product_id, movement_type, quantity_change, notes)
    SELECT OLD.business_id, pc.component_id, 'ADJUSTMENT', OLD.quantity * pc.quantity,
           'Reversion por eliminacion de venta (compuesto)'
      FROM product_components pc
      JOIN businesses b ON b.id = pc.business_id AND b.composites_enabled
     WHERE pc.business_id = OLD.business_id AND pc.product_id = OLD.product_id;
    IF NOT FOUND THEN
        INSERT INTO inventory_movements (business_id, product_id, movement_type, quantity_change, notes)
        VALUES (OLD.business_id, OLD.product_id, 'ADJUSTMENT', OLD.quantity, 'Reversion por eliminacion de venta');
    END IF;
    RETURN OLD;
END;
$$;

-- 5. Inventario: el stock de un compuesto = cuántos se pueden armar con lo que hay.
CREATE OR REPLACE VIEW v_inventory WITH (security_invoker = true) AS
SELECT
    p.id            AS product_id,
    p.business_id,
    p.name,
    c.name          AS category,
    s.name          AS supplier,
    p.price,
    COALESCE(k.stock, p.stock_quantity) AS stock_quantity,
    p.min_stock,
    p.lead_time_days,
    CASE
        WHEN COALESCE(k.stock, p.stock_quantity) = 0            THEN 'AGOTADO'
        WHEN COALESCE(k.stock, p.stock_quantity) < p.min_stock  THEN 'BAJO'
        ELSE 'NORMAL'
    END             AS status
FROM products p
JOIN businesses b ON b.id = p.business_id
LEFT JOIN categories c ON c.id = p.category_id
LEFT JOIN suppliers  s ON s.id = p.supplier_id
LEFT JOIN LATERAL (
    SELECT MIN(cp.stock_quantity / pc.quantity) AS stock   -- sin receta: NULL -> stock propio
      FROM product_components pc
      JOIN products cp ON cp.id = pc.component_id
     WHERE pc.product_id = p.id AND b.composites_enabled
) k ON true
WHERE p.is_active;

COMMIT;
