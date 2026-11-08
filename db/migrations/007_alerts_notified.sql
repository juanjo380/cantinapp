-- =============================================================================
-- 007 - Alertas automáticas: marca de "ya se avisó por correo"
-- Ejecutar en: Supabase Dashboard -> SQL Editor, DESPUES de 006 y ANTES de
-- desplegar el backend que la usa (sin ella el trabajo diario da 500).
-- Idempotente: se puede ejecutar más de una vez.
-- =============================================================================
BEGIN;

-- El correo-resumen diario incluye solo las alertas pendientes sin notified_at y
-- max(notified_at) evita mandar dos correos el mismo día.
ALTER TABLE alerts ADD COLUMN IF NOT EXISTS notified_at timestamptz;
CREATE INDEX IF NOT EXISTS ix_alerts_business_unnotified
    ON alerts (business_id) WHERE status = 'PENDING' AND notified_at IS NULL;

COMMIT;
