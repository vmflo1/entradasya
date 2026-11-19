-- orders_db: órdenes de compra y su estado
CREATE TABLE IF NOT EXISTS ordenes (
    id              UUID          PRIMARY KEY,
    usuario_id      INTEGER       NOT NULL,
    email           VARCHAR(255)  NOT NULL,
    evento_id       INTEGER       NOT NULL,
    sector_id       INTEGER       NOT NULL,
    cantidad        INTEGER       NOT NULL CHECK (cantidad BETWEEN 1 AND 6),
    precio_unitario NUMERIC(10,2),
    total           NUMERIC(10,2),
    evento_nombre   VARCHAR(150),
    evento_fecha    TIMESTAMPTZ,
    evento_lugar    VARCHAR(150),
    sector_nombre   VARCHAR(60),
    estado          VARCHAR(20)   NOT NULL DEFAULT 'pendiente'
                    CHECK (estado IN ('pendiente', 'pagada', 'rechazada', 'cancelada')),
    motivo          TEXT,
    entradas_emitidas BOOLEAN     NOT NULL DEFAULT FALSE,
    correo_enviado  BOOLEAN       NOT NULL DEFAULT FALSE,
    creado_en       TIMESTAMPTZ   NOT NULL DEFAULT now(),
    actualizado_en  TIMESTAMPTZ   NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_ordenes_usuario ON ordenes(usuario_id);
