-- =============================================================================
-- 012 - Descuentos: fecha del último descuento (no volver a sugerirlo antes de ver su efecto) y
--       precio de lista mientras el descuento está activo (viñeta «−N%» y botón «Quitar descuento»).
-- Ejecutar en: Supabase Dashboard -> SQL Editor, DESPUES de 001-011.
-- Debe ejecutarse ANTES de desplegar el backend que la usa (solo /api/products/discounts* la lee).
-- =============================================================================
ALTER TABLE products ADD COLUMN IF NOT EXISTS last_discount_at timestamptz;
ALTER TABLE products ADD COLUMN IF NOT EXISTS price_before_discount numeric(12,2)
    CHECK (price_before_discount >= 0);  -- NULL = sin descuento activo
