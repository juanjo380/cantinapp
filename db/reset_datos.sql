-- =============================================================================
-- RESET DE DATOS - deja la base VACÍA (borra usuarios, negocios, productos, ventas,
-- predicciones, alertas... TODO). Conserva el esquema: tablas, vistas, triggers,
-- índices, RLS y migraciones aplicadas. NO se puede deshacer.
--
-- Uso: Supabase Dashboard -> SQL Editor -> pegar y ejecutar. Supabase avisará que es
-- una operación destructiva: confirmar solo si de verdad quieres empezar de cero.
-- Antes, si hay algo que conservar: Database -> Backups (o exporta las tablas a CSV).
--
-- La app usa su propia tabla `users` (no Supabase Auth), así que no hay nada que borrar
-- en el esquema `auth`. Después, regístrate de nuevo en la app.
-- =============================================================================
BEGIN;

TRUNCATE TABLE
    alerts,
    recommendations,
    product_cooccurrences,
    forecasts,
    inventory_movements,
    sales,
    sales_imports,
    product_components,
    products,
    categories,
    suppliers,
    business_invitations,
    email_codes,
    business_locations,
    business_members,
    user_consents,
    users,
    businesses
RESTART IDENTITY CASCADE;

COMMIT;

-- Verificación: todas deben dar 0
SELECT 'businesses' AS tabla, count(*) FROM businesses
UNION ALL SELECT 'users', count(*) FROM users
UNION ALL SELECT 'products', count(*) FROM products
UNION ALL SELECT 'sales', count(*) FROM sales
UNION ALL SELECT 'forecasts', count(*) FROM forecasts
UNION ALL SELECT 'alerts', count(*) FROM alerts;
