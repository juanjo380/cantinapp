-- =============================================================================
-- 009 - Ventas por sede, sede asignada a cada persona del equipo y cuentas sin negocio
-- Ejecutar en: Supabase Dashboard -> SQL Editor, DESPUES de 001-008.
-- Debe ejecutarse ANTES de desplegar el backend que la usa (sin ella todo da 500).
-- =============================================================================
BEGIN;

-- 1. Cuentas sin negocio (quien se registra para aceptar una invitación):
--    sus autorizaciones del registro no pertenecen a ningún negocio.
ALTER TABLE user_consents ALTER COLUMN business_id DROP NOT NULL;

-- 2. Sede de cada venta. NULL = venta del negocio sin sede (las anteriores a esta migración).
--    La FK compuesta garantiza que la sede sea del mismo negocio.
ALTER TABLE sales ADD COLUMN location_id uuid;
ALTER TABLE sales ADD CONSTRAINT fk_sales_location
    FOREIGN KEY (business_id, location_id) REFERENCES business_locations (business_id, id);
CREATE INDEX ix_sales_business_location_date ON sales (business_id, location_id, sale_date)
    WHERE location_id IS NOT NULL;

-- 3. Sede asignada a cada persona del equipo. NULL = todas las sedes (el dueño siempre ve todas).
ALTER TABLE business_members ADD COLUMN location_id uuid;
ALTER TABLE business_members ADD CONSTRAINT fk_business_members_location
    FOREIGN KEY (business_id, location_id) REFERENCES business_locations (business_id, id);

-- 4. Sede con la que entra quien acepta la invitación. Borrar la sede anula sus invitaciones.
ALTER TABLE business_invitations ADD COLUMN location_id uuid;
ALTER TABLE business_invitations ADD CONSTRAINT fk_business_invitations_location
    FOREIGN KEY (business_id, location_id) REFERENCES business_locations (business_id, id) ON DELETE CASCADE;

COMMIT;
