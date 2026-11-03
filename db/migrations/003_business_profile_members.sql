-- =============================================================================
-- 003 - Perfil de negocio y de usuario, sedes y multi-negocio (miembros con rol)
-- Ejecutar en: Supabase Dashboard -> SQL Editor, DESPUES de 001 y 002.
-- Debe ejecutarse ANTES de desplegar el backend que la usa (sin ella todo da 500).
-- =============================================================================
BEGIN;

-- 1. Perfil del negocio (todos opcionales: se completan despues del registro)
ALTER TABLE businesses
    ADD COLUMN legal_name    text,          -- razon social
    ADD COLUMN tax_id        text,          -- NIT, p. ej. 900123456-7
    ADD COLUMN business_type text,          -- tienda, cantina escolar, cafeteria...
    ADD COLUMN phone         text,
    ADD COLUMN email         text,
    ADD COLUMN address       text,
    ADD COLUMN city          text,
    ADD COLUMN department    text;

-- 2. Perfil del usuario
ALTER TABLE users
    ADD COLUMN phone     text,
    ADD COLUMN job_title text;              -- cargo
-- Un usuario puede pertenecer a varios negocios (business_members); esta columna
-- queda como "ultimo negocio usado" para abrir sesion en el.
ALTER TABLE users ALTER COLUMN business_id DROP NOT NULL;
COMMENT ON COLUMN users.business_id IS 'Ultimo negocio usado; la pertenencia real esta en business_members';

-- 3. Miembros: quien pertenece a que negocio y con que rol
CREATE TABLE business_members (                   -- [Modulo Auth]
    business_id  uuid        NOT NULL REFERENCES businesses (id),
    user_id      uuid        NOT NULL REFERENCES users (id),
    role         text        NOT NULL CHECK (role IN ('OWNER', 'ADMIN', 'MEMBER')),
    created_at   timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (business_id, user_id)
);
CREATE INDEX ix_business_members_user ON business_members (user_id);
-- Un solo dueno por negocio
CREATE UNIQUE INDEX ux_business_members_owner ON business_members (business_id) WHERE role = 'OWNER';

-- Datos existentes: el primer usuario de cada negocio queda como dueno, el resto como admin
INSERT INTO business_members (business_id, user_id, role)
SELECT business_id,
       id,
       CASE WHEN row_number() OVER (PARTITION BY business_id ORDER BY created_at, id) = 1
            THEN 'OWNER' ELSE 'ADMIN' END
FROM users
WHERE business_id IS NOT NULL;

-- 4. Sedes del negocio (datos de perfil; el inventario sigue siendo del negocio)
CREATE TABLE business_locations (                 -- [Modulo Negocio]
    id           uuid        PRIMARY KEY DEFAULT gen_random_uuid(),
    business_id  uuid        NOT NULL REFERENCES businesses (id),
    name         text        NOT NULL CHECK (length(trim(name)) > 0),
    address      text,
    city         text,
    phone        text,
    is_main      boolean     NOT NULL DEFAULT false,
    created_at   timestamptz NOT NULL DEFAULT now(),
    updated_at   timestamptz NOT NULL DEFAULT now(),
    UNIQUE (business_id, id)
);
CREATE UNIQUE INDEX ux_business_locations_main ON business_locations (business_id) WHERE is_main;
CREATE TRIGGER trg_business_locations_updated BEFORE UPDATE ON business_locations
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();

-- Mismo criterio que schema.sql seccion 9: solo el backend accede
ALTER TABLE business_members   ENABLE ROW LEVEL SECURITY;
ALTER TABLE business_locations ENABLE ROW LEVEL SECURITY;
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'anon') THEN
        REVOKE ALL ON business_members, business_locations FROM anon;
    END IF;
    IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'authenticated') THEN
        REVOKE ALL ON business_members, business_locations FROM authenticated;
    END IF;
END;
$$;

COMMIT;
