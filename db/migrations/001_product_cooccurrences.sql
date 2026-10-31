-- =============================================================================
-- 001 - Co-ocurrencia temporal de picos de venta (recomendaciones Fase 1)
-- Ejecutar en: Supabase Dashboard -> SQL Editor, sobre una BD con schema.sql aplicado.
-- =============================================================================
BEGIN;

CREATE TABLE product_cooccurrences (              -- [Modulo Recomendacion]
    business_id        uuid         NOT NULL REFERENCES businesses (id),
    product_id         uuid         NOT NULL,     -- A: producto con el pico
    related_product_id uuid         NOT NULL,     -- B: producto que sube en los dias siguientes
    peaks              integer      NOT NULL CHECK (peaks > 0),
    hits               integer      NOT NULL CHECK (hits > 0),
    score              numeric(5,4) NOT NULL CHECK (score BETWEEN 0 AND 1),   -- hits / peaks
    computed_at        timestamptz  NOT NULL DEFAULT now(),
    PRIMARY KEY (business_id, product_id, related_product_id),
    FOREIGN KEY (business_id, product_id)         REFERENCES products (business_id, id),
    FOREIGN KEY (business_id, related_product_id) REFERENCES products (business_id, id),
    CHECK (product_id <> related_product_id)
);

-- Mismo criterio que schema.sql seccion 9: solo el backend accede
ALTER TABLE product_cooccurrences ENABLE ROW LEVEL SECURITY;
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'anon') THEN
        REVOKE ALL ON product_cooccurrences FROM anon;
    END IF;
    IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'authenticated') THEN
        REVOKE ALL ON product_cooccurrences FROM authenticated;
    END IF;
END;
$$;

COMMIT;
