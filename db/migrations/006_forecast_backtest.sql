-- =============================================================================
-- 006 - Predicción con estacionalidad semanal, modo AUTO y métricas de backtest
-- Ejecutar en: Supabase Dashboard -> SQL Editor, DESPUES de 005 y ANTES de
-- desplegar el backend que la usa (sin ella toda predicción nueva da 500/422).
-- Idempotente: se puede ejecutar más de una vez.
-- =============================================================================
BEGIN;

-- 1. Nuevo modelo. model_type guarda el modelo que se usó (nunca AUTO).
--    El CHECK en línea de schema.sql recibe el nombre por defecto forecasts_model_type_check.
ALTER TABLE forecasts DROP CONSTRAINT IF EXISTS forecasts_model_type_check;
ALTER TABLE forecasts ADD CONSTRAINT forecasts_model_type_check
    CHECK (model_type IN ('LINEAR_REGRESSION', 'MOVING_AVERAGE', 'SEASONAL_WEEKLY'));

-- 2. Modelo pedido (AUTO o uno concreto) y error del backtest de los últimos 14 días.
--    NULL en las predicciones anteriores a esta migración.
ALTER TABLE forecasts ADD COLUMN IF NOT EXISTS requested_model text;
ALTER TABLE forecasts ADD COLUMN IF NOT EXISTS backtest_wape   numeric(10,4);   -- Σ|error| / Σ real
ALTER TABLE forecasts ADD COLUMN IF NOT EXISTS backtest_mae    numeric(14,4);   -- unidades por día

ALTER TABLE forecasts DROP CONSTRAINT IF EXISTS forecasts_requested_model_check;
ALTER TABLE forecasts ADD CONSTRAINT forecasts_requested_model_check
    CHECK (requested_model IN ('AUTO', 'LINEAR_REGRESSION', 'MOVING_AVERAGE', 'SEASONAL_WEEKLY'));

COMMIT;
