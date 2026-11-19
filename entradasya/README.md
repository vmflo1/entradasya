# EntradasYa v1

Plataforma de venta de entradas: proyecto de clase del módulo **Contenedores y Orquestación**.
Versión 1: **8 servicios independientes en Python** que se comunican **solo por HTTP/JSON**, cada uno con
**su propia base de datos**, detrás de **Nginx**, instalados a mano en Ubuntu y desplegados con un **pipeline por servicio**. Sin contenedores.

## Los tres roles

| Rol | Qué hace | Dónde |
|---|---|---|
| **Cliente** | Se registra, ve la cartelera, compra (máx. 6), paga, recibe el correo y descarga sus entradas (PDF + QR) | `/`, `/mis-entradas` |
| **Organizador** | Panel **Eventos**: los de hoy, los próximos y los anteriores, con filtro por mes y día (ve sus eventos y los cargados en el sistema sin organizador, como los de prueba); crea eventos (Nuevo evento); edita nombre, fecha y sectores (precio y cupo), sube la imagen, publica o cancela; ve ventas, ingresos y asistentes | `/organizador`, `/organizador/nuevo` |
| **Portero** | Panel **Eventos**: los de hoy y todos los próximos (puede filtrar por mes); al elegir uno abre su **Control de ingresos**: capacidad, vendidos, escaneados, faltantes y disponibles por zona, y escanea el QR o escribe el código | `/portero`, `/portero/evento/{id}` |

Cada rol ve en el menú solo sus secciones. El registro de la web **siempre crea clientes**. Los organizadores y porteros los crea un administrador (ver más abajo).

## Servicios y puertos

| Servicio | Puerto | Base de datos | Qué hace |
|---|---|---|---|
| web | 8000 | — | Pantallas de los tres roles |
| auth | 8001 | auth_db | Registro, login y JWT (id, rol, correo, nombre) |
| events | 8002 | events_db | Eventos, sectores, cupos, imagen; reserva y libera cupos |
| orders | 8003 | orders_db | Orquesta la compra; ventas e ingresos para el organizador |
| payments | 8004 | payments_db | Pago simulado (interno, no expuesto por Nginx) |
| tickets | 8005 | tickets_db | Código único, QR y PDF por entrada; validación de códigos |
| notifications | 8006 | — | Correo de confirmación a Mailpit (interno, no expuesto) |
| checkin | 8007 | checkin_db | Registra el ingreso; rechaza inválidos, de otro evento o ya usados |
| **Nginx** | **8080** (Windows) / **80** (Ubuntu) | — | Única puerta de entrada |
| Mailpit | 1025 / 8025 | — | SMTP de prueba / página para ver los correos |

---

## Ejecutar en Windows

### 1. Requisitos (una sola vez)

1. **Python 3.11 o superior**: https://www.python.org/downloads/ (marque *Add python.exe to PATH*).
2. **PostgreSQL** (versión 18), encendido.
3. **Mailpit** en `C:\mailpit\mailpit.exe`: https://github.com/axllent/mailpit/releases (`mailpit-windows-amd64.zip`).
4. **Nginx** en `C:\nginx\nginx.exe`: https://nginx.org/en/download.html (versión *Stable* para Windows).

### 2. Preparar (una sola vez, y después de cada actualización)

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\setup.ps1
```

Crea los `.env` que falten (y agrega variables nuevas a los existentes sin tocar las que ya tiene),
crea las 6 bases de datos y sus usuarios (le pide la contraseña de `postgres`) e instala las dependencias.

### 3. Crear el organizador y el portero de prueba

```powershell
cd services\auth
.\.venv\Scripts\python.exe -m app.cli --nombre "Olga Organizadora" --email organizador@prueba.com --password clave123 --rol organizador
.\.venv\Scripts\python.exe -m app.cli --nombre "Pedro Portero" --email portero@prueba.com --password clave123 --rol portero
cd ..\..
```

### 4. Iniciar y detener

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\start.ps1
powershell -ExecutionPolicy Bypass -File .\scripts\stop.ps1
```

**Web:** http://localhost:8080 · **Correos:** http://localhost:8025

---

## Ejecutar en Ubuntu (modo prueba, con scripts)

```bash
sudo apt install -y python3 python3-venv postgresql nginx curl
sudo bash < <(curl -sL https://raw.githubusercontent.com/axllent/mailpit/develop/install.sh)
mailpit &

bash scripts/setup.sh
cd services/auth
.venv/bin/python -m app.cli --nombre "Olga Organizadora" --email organizador@prueba.com --password clave123 --rol organizador
.venv/bin/python -m app.cli --nombre "Pedro Portero" --email portero@prueba.com --password clave123 --rol portero
cd ../..
bash scripts/start.sh                      # logs en logs/, detener con: bash scripts/stop.sh

sudo cp infra/nginx/entradasya.conf /etc/nginx/sites-available/entradasya
sudo ln -sf /etc/nginx/sites-available/entradasya /etc/nginx/sites-enabled/entradasya
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t && sudo systemctl reload nginx
```

En Ubuntu Nginx usa el puerto 80: ponga `PUBLIC_URL=http://localhost` (o la IP del servidor) en `services/orders/.env`.

---

## Servidor Ubuntu y pipeline (criterio de aceptación 4)

### 1. Instalar el servidor (una vez)

Deja los 8 servicios como servicios del sistema (`entradasya@<servicio>`, systemd) en `/opt/entradasya`,
que arrancan solos al encender la máquina, con Nginx en el puerto 80.

```bash
bash scripts/stop.sh                                   # si estaba usando el modo prueba
sudo bash infra/scripts/instalar_servidor.sh <usuario>  # <usuario>: quien ejecuta los despliegues
```

`<usuario>` puede ejecutar **solo** `/usr/local/bin/entradasya-desplegar` con `sudo`, sin contraseña.

### 2. Conectar GitHub

1. Suba el proyecto a un repositorio de GitHub (rama `main`).
2. Elija el modo de despliegue en **Settings → Secrets and variables → Actions → Variables** → `DEPLOY_MODO`:

| Modo | Cuándo | Qué configurar |
|---|---|---|
| `self-hosted` (por defecto) | El servidor **no** tiene IP pública (laptop, VM local) | En **Settings → Actions → Runners → New self-hosted runner** siga los pasos en el servidor, con el mismo `<usuario>` del paso 1 |
| `ssh` | El servidor tiene IP accesible (AWS, Azure) | Secrets `SSH_HOST`, `SSH_USER` (= `<usuario>`), `SSH_KEY` (clave privada) y opcional `SSH_PORT` |

### 3. Cómo funciona

Hay **un pipeline por servicio** (`.github/workflows/desplegar-<servicio>.yml`). Cada push a `main` que cambie
`services/<servicio>/` ejecuta:

1. **Verificar:** instala dependencias, compila el código y comprueba que no haya puertos ni direcciones escritas en el código.
2. **Desplegar:** copia el código a `/opt/entradasya/services/<servicio>` (sin tocar `.env`, `.venv` ni `data`),
   instala dependencias, reinicia `entradasya@<servicio>` y espera a que `/health` responda 200. Si no responde, el pipeline falla.

También se puede lanzar a mano desde la pestaña **Actions → Desplegar <servicio> → Run workflow**.

Logs de un servicio en el servidor: `journalctl -u entradasya@<servicio> -f`

---

## Probar los flujos

**Cliente:** cartelera → evento → sector → cantidad → tarjeta `4111 1111 1111 1111`, vencimiento `12/30`, CVV `123` (o **Pago con QR** → *Ya pagué*) → Confirmar compra →
correo en Mailpit → Mis entradas → Descargar PDF. Tarjetas terminadas en `0000` se rechazan.

**Organizador** (`organizador@prueba.com` / `clave123`): Panel → Nuevo evento (nace en borrador) →
agregar sectores → subir imagen → Publicar. Aparece en la cartelera. Ventas, ingresos y asistentes se ven en el mismo panel.

**Portero** (`portero@prueba.com` / `clave123`): Eventos → elegir el evento (hoy o del mes) → Control de ingresos → escanear el QR o escribir el código.
El primer escaneo dice **Ingreso permitido**; el segundo del mismo código, **Entrada ya utilizada** con la hora del primer ingreso.

> La cámara del celular solo funciona con **HTTPS** o desde **localhost**. Por HTTP con la IP del servidor, escriba el código.

## Tipografía

Una sola familia en todo el sistema: **Helvetica / Arial** (la misma del texto del logo). Títulos en negrita y textos en regular, en la web, el correo y el PDF. No hace falta copiar archivos de fuentes.

## Cumplimiento de los requerimientos técnicos

1. Configuración en variables de entorno (`.env` de cada servicio).
2. Una BD por servicio: cada usuario de PostgreSQL solo puede conectarse a la suya.
3. Solo HTTP + JSON entre servicios.
4. Timeout en toda llamada (`HTTP_TIMEOUT` en orders y checkin).
5. `GET /health` en cada servicio (revisa la BD o el servidor de correo).
6. Logs en consola (o journal) con fecha, nivel y mensaje.
7. README en cada servicio.
8. `BITACORA.md` con los problemas de instalación y despliegue.

Rutas internas protegidas: Nginx bloquea `/api/events/reservas` y `/api/tickets/entradas/generar`;
payments y notifications no se exponen y exigen la clave interna `INTERNAL_API_KEY`.
Cada servicio valida el JWT por su cuenta y revisa el rol (organizador, portero) en sus rutas.
