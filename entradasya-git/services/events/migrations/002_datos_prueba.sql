-- Datos de prueba: solo se cargan si la tabla de eventos está vacía.
-- (Las pantallas del organizador para crear eventos vendrán después.)
DO $$
DECLARE
    e INTEGER;
BEGIN
    IF EXISTS (SELECT 1 FROM eventos) THEN
        RETURN;
    END IF;

    INSERT INTO eventos (nombre, fecha, lugar, descripcion, estado)
    VALUES ('Noche de Charangos', '2026-12-12 20:30:00-04', 'Teatro al Aire Libre, La Paz',
            'Una noche de música andina con los mejores charanguistas del país.', 'publicado')
    RETURNING id INTO e;
    INSERT INTO sectores (evento_id, nombre, precio, cupo_total, cupo_disponible) VALUES
        (e, 'VIP',         350.00,  80,  80),
        (e, 'Preferencia', 220.00, 200, 200),
        (e, 'General',     120.00, 500, 500);

    INSERT INTO eventos (nombre, fecha, lugar, descripcion, estado)
    VALUES ('Festival Rock del Valle', '2027-01-23 18:00:00-04', 'Coliseo Cerrado, Cochabamba',
            'Seis bandas, una sola noche. Rock nacional de principio a fin.', 'publicado')
    RETURNING id INTO e;
    INSERT INTO sectores (evento_id, nombre, precio, cupo_total, cupo_disponible) VALUES
        (e, 'VIP',         400.00, 100, 100),
        (e, 'Preferencia', 250.00, 300, 300),
        (e, 'General',     150.00, 800, 800);

    INSERT INTO eventos (nombre, fecha, lugar, descripcion, estado)
    VALUES ('Sinfonía de Verano', '2027-02-06 19:30:00-04', 'Teatro Municipal, Santa Cruz',
            'La orquesta sinfónica interpreta clásicos del cine y la ópera.', 'publicado')
    RETURNING id INTO e;
    INSERT INTO sectores (evento_id, nombre, precio, cupo_total, cupo_disponible) VALUES
        (e, 'Platea',  280.00, 150, 150),
        (e, 'Palco',   200.00,  60,  60),
        (e, 'Galería',  90.00, 250, 250);

    -- Evento con muy pocos cupos para probar el caso "Agotado"
    INSERT INTO eventos (nombre, fecha, lugar, descripcion, estado)
    VALUES ('Sesión Acústica Íntima', '2026-12-19 21:00:00-04', 'Café Cultural, Sucre',
            'Formato pequeño: pocas entradas, mucha cercanía.', 'publicado')
    RETURNING id INTO e;
    INSERT INTO sectores (evento_id, nombre, precio, cupo_total, cupo_disponible) VALUES
        (e, 'Mesa',    180.00, 2, 2),
        (e, 'General', 100.00, 4, 4);

    -- Evento en borrador: NO debe aparecer en la cartelera
    INSERT INTO eventos (nombre, fecha, lugar, descripcion, estado)
    VALUES ('Evento en preparación', '2027-03-01 20:00:00-04', 'Por definir',
            'Este evento está en borrador.', 'borrador')
    RETURNING id INTO e;
    INSERT INTO sectores (evento_id, nombre, precio, cupo_total, cupo_disponible) VALUES
        (e, 'General', 100.00, 100, 100);
END $$;
