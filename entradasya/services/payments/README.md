# payments

Pasarela de pago **simulada** (sin dinero real). Rechaza las tarjetas que terminan en `REJECT_SUFFIX` (0000). No cobra dos veces la misma orden. Guarda solo los últimos 4 dígitos. Acepta dos métodos simulados: `tarjeta` y `qr` (el QR se aprueba cuando el cliente confirma el pago). El código de seguridad (CVV) nunca llega a este servicio.

- **Puerto:** 8004
- **Datos que guarda:** payments_db
- **Se comunica con:** Ninguno. Solo responde a orders. Nginx no lo expone.

## Requisitos

- Python 3.11 o superior
- PostgreSQL con la base `payments_db` y el usuario `payments_user` (los crea `infra/postgres/01_crear_bases.sql`)

## Variables de entorno

Se leen del archivo `.env` de esta carpeta (copie `.env.example` y complete los valores):

`SERVICE_NAME`, `HOST`, `PORT`, `LOG_LEVEL`, `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_TIMEZONE`, `INTERNAL_API_KEY`, `REJECT_SUFFIX`

## Endpoints

| Ruta | Descripción |
|---|---|
| `POST /pagos` | Procesa el pago (requiere cabecera `X-Internal-Key`) |
| `GET /pagos/{orden_id}` | Consulta el resultado |
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
Chequeo de salud: `http://127.0.0.1:8004/health`

## Despliegue

En el servidor Ubuntu corre como `entradasya@payments` (systemd). Cada push a `main` que cambie `services/payments/`
dispara el pipeline `.github/workflows/desplegar-payments.yml`. Logs: `journalctl -u entradasya@payments -f`.

> Lo normal es preparar e iniciar todos los servicios juntos con los scripts de la carpeta `scripts/` (ver el README principal).
