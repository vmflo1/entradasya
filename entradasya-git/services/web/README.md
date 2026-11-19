# web

Interfaz única para los tres roles: cliente (cartelera, compra, mis entradas), organizador (panel de eventos, sectores, imagen, ventas) y portero (control de ingreso con QR). No guarda datos: el navegador llama a los demás servicios a través de Nginx (`/api/...`).

- **Puerto:** 8000
- **Datos que guarda:** —
- **Se comunica con:** Todos los servicios, siempre a través de Nginx.

## Requisitos

- Python 3.11 o superior
- Nginx delante (la web llama a `/api/...`)

## Variables de entorno

Se leen del archivo `.env` de esta carpeta (copie `.env.example` y complete los valores):

`SERVICE_NAME`, `HOST`, `PORT`, `LOG_LEVEL`

## Endpoints

| Ruta | Descripción |
|---|---|
| `GET /` | Cartelera |
| `GET /evento/{id}` | Mapa de sectores y compra |
| `GET /confirmacion/{orden_id}` | Compra exitosa |
| `GET /mis-entradas` | Entradas y compras del cliente |
| `GET /organizador` | Panel del organizador |
| `GET /organizador/evento/{id}` | Editar evento, sectores, estado, imagen, ventas |
| `GET /portero` | Control de ingreso (escanear o escribir código) |
| `GET /login, /registro` | Cuenta |
| `GET /health` | Salud |

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

Chequeo de salud: `http://127.0.0.1:8000/health`

## Despliegue

En el servidor Ubuntu corre como `entradasya@web` (systemd). Cada push a `main` que cambie `services/web/`
dispara el pipeline `.github/workflows/desplegar-web.yml`. Logs: `journalctl -u entradasya@web -f`.

> Lo normal es preparar e iniciar todos los servicios juntos con los scripts de la carpeta `scripts/` (ver el README principal).
