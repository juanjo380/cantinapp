-- =============================================================================
-- 011 - Los compuestos son un tipo de producto (products.is_composite) que se crea
--       desde la seccion Compuestos: tiene precio, pero su stock sale de la receta.
-- Ejecutar en: Supabase Dashboard -> SQL Editor, DESPUES de 001-010.
-- Debe ejecutarse ANTES de desplegar el backend que la usa (lee products.is_composite).
-- =============================================================================
BEGIN;

ALTER TABLE products ADD COLUMN is_composite boolean NOT NULL DEFAULT false;

-- Los productos que ya tenian receta (creados con 010) pasan a ser compuestos.
UPDATE products SET is_composite = true
 WHERE id IN (SELECT product_id FROM product_components);

-- v_inventory expone is_composite (al final: CREATE OR REPLACE solo permite agregar columnas).
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
    END             AS status,
    p.is_composite
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
