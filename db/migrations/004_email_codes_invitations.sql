-- =============================================================================
-- 004 - Códigos por correo (recuperar contraseña) e invitaciones al equipo
-- Ejecutar en: Supabase Dashboard -> SQL Editor, DESPUES de 001, 002 y 003.
-- Debe ejecutarse ANTES de desplegar el backend que la usa: la validación del
-- token lee users.password_changed_at y sin esa columna todo da 500.
-- =============================================================================
BEGIN;

-- 1. Al cambiar la contraseña se invalidan los tokens emitidos antes (cierra otras sesiones)
ALTER TABLE users ADD COLUMN password_changed_at timestamptz;

-- 2. Códigos de un solo uso enviados por correo. Solo se guarda el hash del código.
CREATE TABLE email_codes (                        -- [Modulo Auth]
    id           uuid        PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id      uuid        NOT NULL REFERENCES users (id),
    purpose      text        NOT NULL CHECK (purpose IN ('PASSWORD_RESET')),
    code_hash    text        NOT NULL,
    attempts     integer     NOT NULL DEFAULT 0,
    expires_at   timestamptz NOT NULL,
    used_at      timestamptz,
    created_at   timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX ix_email_codes_user ON email_codes (user_id, purpose, created_at DESC);

-- 3. Invitaciones: el enlace va al correo invitado; el código de seguridad lo ve solo
--    quien invita y se lo dicta a la persona por otro medio.
CREATE TABLE business_invitations (               -- [Modulo Negocio]
    id           uuid        PRIMARY KEY DEFAULT gen_random_uuid(),
    business_id  uuid        NOT NULL REFERENCES businesses (id),
    email        text        NOT NULL,
    role         text        NOT NULL CHECK (role IN ('ADMIN', 'MEMBER')),
    invited_by   uuid        NOT NULL REFERENCES users (id),
    token_hash   text        NOT NULL UNIQUE,
    code_hash    text        NOT NULL,
    attempts     integer     NOT NULL DEFAULT 0,
    expires_at   timestamptz NOT NULL,
    accepted_at  timestamptz,
    revoked_at   timestamptz,
    created_at   timestamptz NOT NULL DEFAULT now()
);
-- Una sola invitación vigente por correo y negocio (reinvitar anula la anterior)
CREATE UNIQUE INDEX ux_business_invitations_pending
    ON business_invitations (business_id, lower(email)) WHERE accepted_at IS NULL AND revoked_at IS NULL;

-- Mismo criterio que schema.sql sección 9: solo el backend accede
ALTER TABLE email_codes          ENABLE ROW LEVEL SECURITY;
ALTER TABLE business_invitations ENABLE ROW LEVEL SECURITY;
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'anon') THEN
        REVOKE ALL ON email_codes, business_invitations FROM anon;
    END IF;
    IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'authenticated') THEN
        REVOKE ALL ON email_codes, business_invitations FROM authenticated;
    END IF;
END;
$$;

COMMIT;
