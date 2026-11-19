# auth

Usuarios y acceso. Registro (rol cliente), inicio de sesión y emisión del JWT. Contraseñas cifradas con bcrypt. Los organizadores y porteros se crean con la herramienta de administración `app.cli`.

- **Puerto:** 8001
- **Datos que guarda:** auth_db
- **Se comunica con:** Ninguno. Los demás validan el token con el secreto compartido `JWT_SECRET`.

## Requisitos

- Python 3.11 o superior
- PostgreSQL con la base `auth_db` y el usuario `auth_user` (los crea `infra/postgres/01_crear_bases.sql`)

## Variables de entorno

Se leen del archivo `.env` de esta carpeta (copie `.env.example` y complete los valores):

`SERVICE_NAME`, `HOST`, `PORT`, `LOG_LEVEL`, `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_TIMEZONE`, `JWT_SECRET`, `JWT_ALGORITHM`, `JWT_EXPIRES_MINUTES`

## Endpoints

| Ruta | Descripción |
|---|---|
| `POST /registro` | Crea un cliente y devuelve el token |
| `POST /login` | Devuelve el token (JWT con id, rol, correo y nombre) |
| `GET /me` | Datos del usuario del token |
| `GET /health` | Salud y conexión a la BD |

## Ejecutar

Windows (PowerShell, dentro de esta carpeta):

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
copy .env.example .env      # y complete los valores
.\.venv\Scripts\python.exe -m app.main
```

Linux:

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
cp .env.example .env        # y complete los valores
.venv/bin/python -m app.main
```

Al iniciar, el servicio crea sus tablas automáticamente (archivos de `migrations/`).
Chequeo de salud: `http://127.0.0.1:8001/health`

## Crear organizadores y porteros

El registro de la web siempre crea clientes. Para crear (o cambiar de rol) un organizador o portero:

```bash
# Linux
.venv/bin/python -m app.cli --nombre "Olga Organizadora" --email organizador@prueba.com --password clave123 --rol organizador
.venv/bin/python -m app.cli --nombre "Pedro Portero" --email portero@prueba.com --password clave123 --rol portero
```

```powershell
# Windows
.\.venv\Scripts\python.exe -m app.cli --nombre "Olga Organizadora" --email organizador@prueba.com --password clave123 --rol organizador
```

Si el correo ya existe, actualiza su nombre, contraseña y rol.

## Despliegue

En el servidor Ubuntu corre como `entradasya@auth` (systemd). Cada push a `main` que cambie `services/auth/`
dispara el pipeline `.github/workflows/desplegar-auth.yml`. Logs: `journalctl -u entradasya@auth -f`.

> Lo normal es preparar e iniciar todos los servicios juntos con los scripts de la carpeta `scripts/` (ver el README principal).
