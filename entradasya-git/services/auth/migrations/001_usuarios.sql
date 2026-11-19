-- auth_db: usuarios y roles
CREATE TABLE IF NOT EXISTS usuarios (
    id            SERIAL PRIMARY KEY,
    nombre        VARCHAR(100) NOT NULL,
    email         VARCHAR(255) NOT NULL UNIQUE,
    password_hash TEXT         NOT NULL,
    rol           VARCHAR(20)  NOT NULL DEFAULT 'cliente'
                  CHECK (rol IN ('cliente', 'organizador', 'portero')),
    creado_en     TIMESTAMPTZ  NOT NULL DEFAULT now()
);
