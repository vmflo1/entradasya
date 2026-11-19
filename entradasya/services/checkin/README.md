# checkin

Control de ingreso en la puerta. Registra el ingreso o lo rechaza indicando el motivo: código inválido, entrada de otro evento o entrada ya utilizada (con la hora del primer ingreso). Cada entrada sirve una sola vez, aunque dos porteros la escaneen al mismo tiempo (restricción UNIQUE). Cuenta cuántas personas ingresaron.

- **Puerto:** 8007
- **Datos que guarda:** checkin_db
- **Se comunica con:** tickets (para validar el código, con timeout `HTTP_TIMEOUT`).

## Requisitos

- Python 3.11 o superior
- PostgreSQL con la base `checkin_db` y el usuario `checkin_user` (los crea `infra/postgres/01_crear_bases.sql`)

## Variables de entorno

Se leen del archivo `.env` de esta carpeta (copie `.env.example` y complete los valores):

`SERVICE_NAME`, `HOST`, `PORT`, `LOG_LEVEL`, `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_TIMEZONE`, `JWT_SECRET`, `JWT_ALGORITHM`, `TICKETS_URL`, `HTTP_TIMEOUT`

## Endpoints

| Ruta | Descripción |
|---|---|
| `POST /ingresos` | Registrar ingreso `{codigo, evento_id}` (solo portero) |
| `GET /eventos/{evento_id}/asistentes` | Personas que ingresaron (portero u organizador) |
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
Chequeo de salud: `http://127.0.0.1:8007/health`

## Despliegue

En el servidor Ubuntu corre como `entradasya@checkin` (systemd). Cada push a `main` que cambie `services/checkin/`
dispara el pipeline `.github/workflows/desplegar-checkin.yml`. Logs: `journalctl -u entradasya@checkin -f`.

> Lo normal es preparar e iniciar todos los servicios juntos con los scripts de la carpeta `scripts/` (ver el README principal).
