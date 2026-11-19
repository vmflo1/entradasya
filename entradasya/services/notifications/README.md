# notifications

Correos del sistema. Envía la confirmación de compra con el enlace a las entradas. En la v1 los correos van a Mailpit (no se envía nada real).

- **Puerto:** 8006
- **Datos que guarda:** — (solo logs)
- **Se comunica con:** Mailpit por SMTP. Nginx no lo expone.

## Requisitos

- Python 3.11 o superior
- Un servidor SMTP (Mailpit en la v1)

## Variables de entorno

Se leen del archivo `.env` de esta carpeta (copie `.env.example` y complete los valores):

`SERVICE_NAME`, `HOST`, `PORT`, `LOG_LEVEL`, `INTERNAL_API_KEY`, `MAIL_HOST`, `MAIL_PORT`, `MAIL_FROM`, `MAIL_USER`, `MAIL_PASSWORD`, `MAIL_STARTTLS`, `MAIL_TIMEOUT`

## Endpoints

| Ruta | Descripción |
|---|---|
| `POST /correos/confirmacion` | Envía la confirmación (requiere `X-Internal-Key`) |
| `GET /health` | Salud y conexión al servidor de correo |

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

Chequeo de salud: `http://127.0.0.1:8006/health`

## Despliegue

En el servidor Ubuntu corre como `entradasya@notifications` (systemd). Cada push a `main` que cambie `services/notifications/`
dispara el pipeline `.github/workflows/desplegar-notifications.yml`. Logs: `journalctl -u entradasya@notifications -f`.

> Lo normal es preparar e iniciar todos los servicios juntos con los scripts de la carpeta `scripts/` (ver el README principal).
