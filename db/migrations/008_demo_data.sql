-- =============================================================================
-- 008 - Datos de ejemplo identificables y eliminables de una vez
-- Ejecutar en: Supabase Dashboard -> SQL Editor, DESPUES de 007 y ANTES de
-- desplegar el backend que la usa (sin ella GET /api/demo da 500).
-- Idempotente: se puede ejecutar más de una vez.
-- =============================================================================
BEGIN;

-- 1. Las ventas de ejemplo llevan source = 'DEMO'.
--    El CHECK en línea de schema.sql recibe el nombre por defecto sales_source_check.
ALTER TABLE sales DROP CONSTRAINT IF EXISTS sales_source_check;
ALTER TABLE sales ADD CONSTRAINT sales_source_check CHECK (source IN ('MANUAL', 'CSV', 'DEMO'));

-- 2. Productos de ejemplo: DELETE /api/demo borra estos y todo lo que cuelga de ellos.
ALTER TABLE products ADD COLUMN IF NOT EXISTS is_demo boolean NOT NULL DEFAULT false;
CREATE INDEX IF NOT EXISTS ix_products_business_demo ON products (business_id) WHERE is_demo;

COMMIT;
