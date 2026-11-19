-- events_db: eventos, sectores (precio y cupo) y reservas de cupo
CREATE TABLE IF NOT EXISTS eventos (
    id             SERIAL PRIMARY KEY,
    nombre         VARCHAR(150) NOT NULL,
    fecha          TIMESTAMPTZ  NOT NULL,
    lugar          VARCHAR(150) NOT NULL,
    imagen         TEXT,
    descripcion    TEXT         NOT NULL DEFAULT '',
    estado         VARCHAR(20)  NOT NULL DEFAULT 'borrador'
                   CHECK (estado IN ('borrador', 'publicado', 'cancelado')),
    organizador_id INTEGER,
    creado_en      TIMESTAMPTZ  NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS sectores (
    id              SERIAL PRIMARY KEY,
    evento_id       INTEGER       NOT NULL REFERENCES eventos(id) ON DELETE CASCADE,
    nombre          VARCHAR(60)   NOT NULL,
    precio          NUMERIC(10,2) NOT NULL CHECK (precio >= 0),
    cupo_total      INTEGER       NOT NULL CHECK (cupo_total >= 0),
    cupo_disponible INTEGER       NOT NULL CHECK (cupo_disponible >= 0),
    CHECK (cupo_disponible <= cupo_total)
);

CREATE INDEX IF NOT EXISTS idx_sectores_evento ON sectores(evento_id);

-- Una reserva por orden: permite liberar los cupos si el pago se rechaza
CREATE TABLE IF NOT EXISTS reservas (
    id          SERIAL PRIMARY KEY,
    orden_id    VARCHAR(64) NOT NULL UNIQUE,
    evento_id   INTEGER     NOT NULL REFERENCES eventos(id),
    sector_id   INTEGER     NOT NULL REFERENCES sectores(id),
    cantidad    INTEGER     NOT NULL CHECK (cantidad BETWEEN 1 AND 6),
    estado      VARCHAR(20) NOT NULL DEFAULT 'reservada'
                CHECK (estado IN ('reservada', 'liberada')),
    creado_en   TIMESTAMPTZ NOT NULL DEFAULT now(),
    liberada_en TIMESTAMPTZ
);
