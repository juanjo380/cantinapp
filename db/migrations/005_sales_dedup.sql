-- =============================================================================
-- 005 - CSV de ventas sin duplicados
-- Ejecutar en: Supabase Dashboard -> SQL Editor, DESPUES de 001-004 y ANTES de
-- desplegar el backend que la usa (sin estas columnas la carga de CSV da 500).
-- Idempotente: se puede ejecutar más de una vez.
-- =============================================================================
BEGIN;

-- 1. Huella del archivo: si ya se importó en el negocio, el backend pide confirmación (409)
ALTER TABLE sales_imports ADD COLUMN IF NOT EXISTS file_hash      text;
ALTER TABLE sales_imports ADD COLUMN IF NOT EXISTS duplicate_rows integer NOT NULL DEFAULT 0;
CREATE INDEX IF NOT EXISTS ix_sales_imports_file_hash
    ON sales_imports (business_id, file_hash) WHERE file_hash IS NOT NULL;

-- 2. Huella por fila: producto|fecha|cantidad|precio|n (n = repetición dentro del archivo).
--    NULL = venta manual o duplicado cargado a propósito (skip_duplicates=false).
ALTER TABLE sales ADD COLUMN IF NOT EXISTS row_hash text;

-- 3. Backfill de las ventas CSV ya cargadas, con la misma fórmula que
--    backend/app/modules/sales/domain/dedup.py. n se numera por negocio (no por archivo):
--    si un CSV ya se había importado dos veces, sus copias quedan con n = 0 y 1 y
--    reimportarlo de nuevo no agrega nada.
UPDATE sales s
SET row_hash = h.row_hash
FROM (
    SELECT id,
           encode(sha256(convert_to(
               product_id::text || '|' || to_char(sale_date, 'YYYY-MM-DD') || '|' || quantity::text
               || '|' || unit_price::numeric(12,2)::text || '|'
               || (row_number() OVER (
                       PARTITION BY business_id, product_id, sale_date, quantity, unit_price
                       ORDER BY created_at, id) - 1)::text,
               'UTF8')), 'hex') AS row_hash
    FROM sales
    WHERE source = 'CSV'
) h
WHERE s.id = h.id AND s.row_hash IS NULL;

CREATE UNIQUE INDEX IF NOT EXISTS ux_sales_business_row_hash
    ON sales (business_id, row_hash) WHERE row_hash IS NOT NULL;

COMMIT;
