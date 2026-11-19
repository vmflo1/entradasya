-- tickets_db: entradas emitidas (los PDF se guardan en la carpeta local)
CREATE TABLE IF NOT EXISTS entradas (
    id            SERIAL PRIMARY KEY,
    codigo        VARCHAR(32)  NOT NULL UNIQUE,
    orden_id      VARCHAR(64)  NOT NULL,
    usuario_id    INTEGER      NOT NULL,
    numero        INTEGER      NOT NULL,   -- 1 de N dentro de la orden
    total_orden   INTEGER      NOT NULL,
    evento_id     INTEGER      NOT NULL,
    evento_nombre VARCHAR(150) NOT NULL,
    evento_fecha  TIMESTAMPTZ  NOT NULL,
    evento_lugar  VARCHAR(150) NOT NULL,
    sector_nombre VARCHAR(60)  NOT NULL,
    estado        VARCHAR(20)  NOT NULL DEFAULT 'valida'
                  CHECK (estado IN ('valida', 'anulada')),
    pdf_archivo   TEXT         NOT NULL,
    creado_en     TIMESTAMPTZ  NOT NULL DEFAULT now(),
    UNIQUE (orden_id, numero)
);

CREATE INDEX IF NOT EXISTS idx_entradas_usuario ON entradas(usuario_id);
CREATE INDEX IF NOT EXISTS idx_entradas_orden   ON entradas(orden_id);
