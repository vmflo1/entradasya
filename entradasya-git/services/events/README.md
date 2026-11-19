# events

Eventos (borrador, publicado o cancelado), sectores con precio y cupo, imagen y reservas. Nunca vende más que el cupo disponible (descuento atómico en PostgreSQL). Cada organizador solo ve y modifica sus propios eventos.

- **Puerto:** 8002
- **Datos que guarda:** events_db (+ carpeta local de imágenes)
- **Se comunica con:** Ninguno. Solo responde.

## Requisitos

- Python 3.11 o superior
- PostgreSQL con la base `events_db` y el usuario `events_user` (los crea `infra/postgres/01_crear_bases.sql`)

## Variables de entorno

Se leen del archivo `.env` de esta carpeta (copie `.env.example` y complete los valores):

`SERVICE_NAME`, `HOST`, `PORT`, `LOG_LEVEL`, `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_TIMEZONE`, `JWT_SECRET`, `JWT_ALGORITHM`, `IMAGES_DIR`

## Endpoints

| Ruta | Descripción |
|---|---|
| `GET /eventos` | Cartelera: solo eventos publicados |
| `GET /eventos/{id}` | Detalle con sectores |
| `GET /imagenes/{archivo}` | Imagen del evento (WebP) |
| `POST /reservas` | Reserva cupos (uso interno de orders; 409 "Agotado") |
| `POST /reservas/{orden_id}/liberar` | Libera cupos (uso interno de orders) |
| `GET /organizador/eventos` | Eventos del organizador |
| `POST /organizador/eventos` | Crear evento (nace en borrador) |
| `GET, PUT /organizador/eventos/{id}` | Ver o editar un evento propio |
| `POST /organizador/eventos/{id}/estado` | Publicar, volver a borrador o cancelar |
| `POST /organizador/eventos/{id}/imagen` | Subir imagen (JPG, PNG o WebP, máximo 5 MB) |
| `POST /organizador/eventos/{id}/sectores` | Agregar sector |
| `PUT, DELETE /organizador/sectores/{id}` | Editar o eliminar sector (el cupo nunca baja de lo vendido) |
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
Chequeo de salud: `http://127.0.0.1:8002/health`

## Despliegue

En el servidor Ubuntu corre como `entradasya@events` (systemd). Cada push a `main` que cambie `services/events/`
dispara el pipeline `.github/workflows/desplegar-events.yml`. Logs: `journalctl -u entradasya@events -f`.

> Lo normal es preparar e iniciar todos los servicios juntos con los scripts de la carpeta `scripts/` (ver el README principal).
