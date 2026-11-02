-- =============================================================================
-- 002 - Autorizaciones del registro (Ley 1581 de 2012: prueba de la autorizacion)
-- Ejecutar en: Supabase Dashboard -> SQL Editor, sobre una BD con schema.sql aplicado.
-- Debe ejecutarse ANTES de desplegar el backend que la usa (si no, /register da 500).
-- =============================================================================
BEGIN;

-- Bitacora de solo insercion: revocar o volver a aceptar = fila nueva; la vigente es la mas reciente.
CREATE TABLE user_consents (                      -- [Modulo Auth]
    id           uuid        PRIMARY KEY DEFAULT gen_random_uuid(),
    business_id  uuid        NOT NULL REFERENCES businesses (id),
    user_id      uuid        NOT NULL REFERENCES users (id),
    document     text        NOT NULL CHECK (document IN ('TERMS', 'PRIVACY', 'COOKIES', 'ML_ANONYMOUS')),
    version      text        NOT NULL,            -- fecha del texto aceptado, p. ej. 2026-11-01
    granted      boolean     NOT NULL,
    created_at   timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX ix_user_consents_user ON user_consents (user_id, document, created_at DESC);

-- Mismo criterio que schema.sql seccion 9: solo el backend accede
ALTER TABLE user_consents ENABLE ROW LEVEL SECURITY;
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'anon') THEN
        REVOKE ALL ON user_consents FROM anon;
    END IF;
    IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'authenticated') THEN
        REVOKE ALL ON user_consents FROM authenticated;
    END IF;
END;
$$;

COMMIT;
