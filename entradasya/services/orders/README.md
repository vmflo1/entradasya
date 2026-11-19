# orders

Compras. Orquesta el flujo: events (reserva) → payments (cobro) → tickets (PDF) → notifications (correo). Si el pago se rechaza, pide liberar los cupos. Si el correo falla, la compra sigue siendo válida. También entrega las ventas e ingresos de cada evento a su organizador.

- **Puerto:** 8003
- **Datos que guarda:** orders_db
- **Se comunica con:** events, payments, tickets y notifications (con timeout `HTTP_TIMEOUT`).

## Requisitos

- Python 3.11 o superior
- PostgreSQL con la base `orders_db` y el usuario `orders_user` (los crea `infra/postgres/01_crear_bases.sql`)

## Variables de entorno

Se leen del archivo `.env` de esta carpeta (copie `.env.example` y complete los valores):

`SERVICE_NAME`, `HOST`, `PORT`, `LOG_LEVEL`, `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_TIMEZONE`, `JWT_SECRET`, `JWT_ALGORITHM`, `EVENTS_URL`, `PAYMENTS_URL`, `TICKETS_URL`, `NOTIFICATIONS_URL`, `INTERNAL_API_KEY`, `HTTP_TIMEOUT`, `PUBLIC_URL`

## Endpoints

| Ruta | Descripción |
|---|---|
| `POST /ordenes` | Compra (máximo 6 entradas). 409 Agotado, 402 Pago rechazado |
| `GET /ordenes/mias` | Historial del cliente |
| `GET /ordenes/{id}` | Detalle de una orden propia |
| `GET /ventas/eventos/{evento_id}` | Ventas e ingresos (solo el organizador del evento) |
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
Chequeo de salud: `http://127.0.0.1:8003/health`

## Despliegue

En el servidor Ubuntu corre como `entradasya@orders` (systemd). Cada push a `main` que cambie `services/orders/`
dispara el pipeline `.github/workflows/desplegar-orders.yml`. Logs: `journalctl -u entradasya@orders -f`.

> Lo normal es preparar e iniciar todos los servicios juntos con los scripts de la carpeta `scripts/` (ver el README principal).

## Pago

`POST /ordenes` recibe `metodo`: `tarjeta` (con `tarjeta_titular`, `tarjeta_numero`, `tarjeta_vencimiento` MM/AA y `tarjeta_cvv`) o `qr`. orders valida los datos; a payments solo envía el método y el número de tarjeta. El CVV nunca se reenvía ni se guarda.
