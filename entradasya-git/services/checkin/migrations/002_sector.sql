-- Zona (sector) de cada ingreso, para el control de ingresos por zona.
-- El dato lo informa tickets al validar el código; checkin guarda su propia copia.
ALTER TABLE ingresos ADD COLUMN IF NOT EXISTS sector_nombre VARCHAR(60);
