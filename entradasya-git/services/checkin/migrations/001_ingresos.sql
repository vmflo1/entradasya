-- checkin_db: ingresos registrados en la puerta
CREATE TABLE IF NOT EXISTS ingresos (
    id             SERIAL PRIMARY KEY,
    codigo         VARCHAR(32)  NOT NULL UNIQUE,   -- una entrada solo puede ingresar una vez
    evento_id      INTEGER      NOT NULL,
    evento_nombre  VARCHAR(150),
    portero_id     INTEGER      NOT NULL,
    portero_nombre VARCHAR(100),
    ingresado_en   TIMESTAMPTZ  NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_ingresos_evento ON ingresos(evento_id);

-- Intentos rechazados (para auditoría del portero)
CREATE TABLE IF NOT EXISTS rechazos (
    id          SERIAL PRIMARY KEY,
    codigo      VARCHAR(64)  NOT NULL,
    evento_id   INTEGER      NOT NULL,
    motivo      TEXT         NOT NULL,
    portero_id  INTEGER      NOT NULL,
    creado_en   TIMESTAMPTZ  NOT NULL DEFAULT now()
);
