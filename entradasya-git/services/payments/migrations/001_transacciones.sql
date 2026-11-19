-- payments_db: transacciones de la pasarela simulada (no se usa dinero real)
CREATE TABLE IF NOT EXISTS transacciones (
    id               SERIAL PRIMARY KEY,
    orden_id         VARCHAR(64)   NOT NULL UNIQUE,  -- impide cobrar dos veces la misma orden
    monto            NUMERIC(10,2) NOT NULL CHECK (monto >= 0),
    tarjeta_ultimos4 CHAR(4)       NOT NULL,         -- nunca se guarda el número completo
    resultado        VARCHAR(20)   NOT NULL CHECK (resultado IN ('aprobado', 'rechazado')),
    motivo           TEXT,
    creado_en        TIMESTAMPTZ   NOT NULL DEFAULT now()
);
