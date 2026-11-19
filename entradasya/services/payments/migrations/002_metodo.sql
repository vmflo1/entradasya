-- Método de pago simulado: tarjeta o QR. Con QR no hay tarjeta, por eso los últimos 4 dígitos pueden ser NULL.
ALTER TABLE transacciones ADD COLUMN IF NOT EXISTS metodo VARCHAR(10) NOT NULL DEFAULT 'tarjeta';
ALTER TABLE transacciones ALTER COLUMN tarjeta_ultimos4 DROP NOT NULL;
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'transacciones_metodo_check') THEN
        ALTER TABLE transacciones ADD CONSTRAINT transacciones_metodo_check CHECK (metodo IN ('tarjeta', 'qr'));
    END IF;
END $$;
