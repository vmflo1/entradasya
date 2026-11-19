-- =====================================================================
-- EntradasYa v1 - Creacion de bases de datos y usuarios (psql)
-- Una base por servicio, cada una con su propio usuario.
-- Ningun usuario puede conectarse a la base de otro servicio.
--
-- Se puede ejecutar varias veces: si algo ya existe, no lo duplica
-- y actualiza la contrasena del usuario.
--
-- IMPORTANTE: se ejecuta con psql (NO con pgAdmin), porque usa variables.
-- Normalmente lo ejecuta scripts/setup.ps1 (Windows) o scripts/setup.sh (Linux).
-- Manualmente:
--   psql -U postgres -v auth_pass=... -v events_pass=... -v orders_pass=... \
--        -v payments_pass=... -v tickets_pass=... -v checkin_pass=... \
--        -f 01_crear_bases.sql
-- =====================================================================
\set ON_ERROR_STOP on

-- ---------- auth ----------
SELECT format('CREATE ROLE auth_user LOGIN PASSWORD %L', :'auth_pass')
WHERE NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'auth_user') \gexec
SELECT format('ALTER ROLE auth_user LOGIN PASSWORD %L', :'auth_pass') \gexec
SELECT 'CREATE DATABASE auth_db OWNER auth_user'
WHERE NOT EXISTS (SELECT 1 FROM pg_database WHERE datname = 'auth_db') \gexec
REVOKE CONNECT ON DATABASE auth_db FROM PUBLIC;
GRANT CONNECT ON DATABASE auth_db TO auth_user;

-- ---------- events ----------
SELECT format('CREATE ROLE events_user LOGIN PASSWORD %L', :'events_pass')
WHERE NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'events_user') \gexec
SELECT format('ALTER ROLE events_user LOGIN PASSWORD %L', :'events_pass') \gexec
SELECT 'CREATE DATABASE events_db OWNER events_user'
WHERE NOT EXISTS (SELECT 1 FROM pg_database WHERE datname = 'events_db') \gexec
REVOKE CONNECT ON DATABASE events_db FROM PUBLIC;
GRANT CONNECT ON DATABASE events_db TO events_user;

-- ---------- orders ----------
SELECT format('CREATE ROLE orders_user LOGIN PASSWORD %L', :'orders_pass')
WHERE NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'orders_user') \gexec
SELECT format('ALTER ROLE orders_user LOGIN PASSWORD %L', :'orders_pass') \gexec
SELECT 'CREATE DATABASE orders_db OWNER orders_user'
WHERE NOT EXISTS (SELECT 1 FROM pg_database WHERE datname = 'orders_db') \gexec
REVOKE CONNECT ON DATABASE orders_db FROM PUBLIC;
GRANT CONNECT ON DATABASE orders_db TO orders_user;

-- ---------- payments ----------
SELECT format('CREATE ROLE payments_user LOGIN PASSWORD %L', :'payments_pass')
WHERE NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'payments_user') \gexec
SELECT format('ALTER ROLE payments_user LOGIN PASSWORD %L', :'payments_pass') \gexec
SELECT 'CREATE DATABASE payments_db OWNER payments_user'
WHERE NOT EXISTS (SELECT 1 FROM pg_database WHERE datname = 'payments_db') \gexec
REVOKE CONNECT ON DATABASE payments_db FROM PUBLIC;
GRANT CONNECT ON DATABASE payments_db TO payments_user;

-- ---------- tickets ----------
SELECT format('CREATE ROLE tickets_user LOGIN PASSWORD %L', :'tickets_pass')
WHERE NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'tickets_user') \gexec
SELECT format('ALTER ROLE tickets_user LOGIN PASSWORD %L', :'tickets_pass') \gexec
SELECT 'CREATE DATABASE tickets_db OWNER tickets_user'
WHERE NOT EXISTS (SELECT 1 FROM pg_database WHERE datname = 'tickets_db') \gexec
REVOKE CONNECT ON DATABASE tickets_db FROM PUBLIC;
GRANT CONNECT ON DATABASE tickets_db TO tickets_user;

-- ---------- checkin ----------
SELECT format('CREATE ROLE checkin_user LOGIN PASSWORD %L', :'checkin_pass')
WHERE NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'checkin_user') \gexec
SELECT format('ALTER ROLE checkin_user LOGIN PASSWORD %L', :'checkin_pass') \gexec
SELECT 'CREATE DATABASE checkin_db OWNER checkin_user'
WHERE NOT EXISTS (SELECT 1 FROM pg_database WHERE datname = 'checkin_db') \gexec
REVOKE CONNECT ON DATABASE checkin_db FROM PUBLIC;
GRANT CONNECT ON DATABASE checkin_db TO checkin_user;
