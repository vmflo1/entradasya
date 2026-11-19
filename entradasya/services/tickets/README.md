# tickets

Entradas. Genera una por asiento, con código único, QR y PDF A6 (ReportLab), guardado en la carpeta `TICKETS_DIR`. Permite descargarlas e informa si un código es válido.

- **Puerto:** 8005
- **Datos que guarda:** tickets_db (+ carpeta local de PDF)
- **Se comunica con:** Ninguno. Responde a orders y a checkin.

## Requisitos

- Python 3.11 o superior
- PostgreSQL con la base `tickets_db` y el usuario `tickets_user` (los crea `infra/postgres/01_crear_bases.sql`)

## Variables de entorno

Se leen del archivo `.env` de esta carpeta (copie `.env.example` y complete los valores):

`SERVICE_NAME`, `HOST`, `PORT`, `LOG_LEVEL`, `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_TIMEZONE`, `JWT_SECRET`, `JWT_ALGORITHM`, `TICKETS_DIR`

## Endpoints

| Ruta | Descripción |
|---|---|
| `POST /entradas/generar` | Genera entradas (uso interno de orders) |
| `GET /entradas/mias` | Entradas del cliente |
| `GET /entradas/{codigo}/pdf` | Descarga el PDF (solo el dueño) |
| `GET /entradas/{codigo}/validar?evento_id=` | Existe, a qué evento pertenece y si es válida (portero u organizador; lo usa checkin). Solo es válida **el día del evento** (zona `DB_TIMEZONE`) |
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
Chequeo de salud: `http://127.0.0.1:8005/health`

## Despliegue

En el servidor Ubuntu corre como `entradasya@tickets` (systemd). Cada push a `main` que cambie `services/tickets/`
dispara el pipeline `.github/workflows/desplegar-tickets.yml`. Logs: `journalctl -u entradasya@tickets -f`.

> Lo normal es preparar e iniciar todos los servicios juntos con los scripts de la carpeta `scripts/` (ver el README principal).
