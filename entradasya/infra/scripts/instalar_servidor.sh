#!/usr/bin/env bash
# EntradasYa v1 - Instalación del servidor Ubuntu (se ejecuta UNA vez).
#
# Deja los 8 servicios corriendo como servicios del sistema (systemd) en /opt/entradasya,
# Nginx en el puerto 80 y todo preparado para que los pipelines desplieguen.
#
# Uso (desde la carpeta del repositorio clonado):
#   sudo bash infra/scripts/instalar_servidor.sh <usuario_del_runner_o_ssh>
#
# <usuario_del_runner_o_ssh>: el usuario de Linux que ejecuta los despliegues
# (el del runner de GitHub Actions o el que usa el pipeline por SSH).
# Ese usuario podrá ejecutar SOLO el script de despliegue con sudo, sin contraseña.
set -euo pipefail

[ "$(id -u)" -eq 0 ] || { echo "Ejecute con sudo" >&2; exit 1; }
DEPLOY_USER="${1:-}"
[ -n "$DEPLOY_USER" ] || { echo "Uso: sudo bash $0 <usuario_que_despliega>" >&2; exit 1; }
id "$DEPLOY_USER" >/dev/null 2>&1 || { echo "No existe el usuario $DEPLOY_USER" >&2; exit 1; }

REPO="$(cd "$(dirname "$0")/../.." && pwd)"
DESTINO=/opt/entradasya
SERVICIOS=(auth events payments tickets notifications orders checkin web)

echo "== 1/6 Paquetes del sistema =="
apt-get update -qq
apt-get install -y -qq python3 python3-venv rsync curl nginx postgresql >/dev/null

echo "== 2/6 Usuario del sistema 'entradasya' =="
id entradasya >/dev/null 2>&1 || useradd --system --home "$DESTINO" --shell /usr/sbin/nologin entradasya

echo "== 3/6 Copiando el proyecto a $DESTINO =="
mkdir -p "$DESTINO"
rsync -a --exclude '.git/' --exclude '.venv/' --exclude '.env' --exclude 'data/' \
  --exclude 'logs/' --exclude 'run/' --exclude '__pycache__/' "$REPO/" "$DESTINO/"

echo "== 4/6 .env, bases de datos y dependencias =="
# Si el repositorio ya tenía .env (de una instalación de prueba), se reutilizan
# para conservar las mismas contraseñas de las bases de datos.
for d in "$REPO"/services/*/; do
  s="$(basename "$d")"
  if [ -f "$d.env" ] && [ ! -f "$DESTINO/services/$s/.env" ]; then cp "$d.env" "$DESTINO/services/$s/.env"; fi
done
# setup.sh crea los .env que falten (conserva los existentes) y las bases de datos
bash "$DESTINO/scripts/setup.sh"
SERVIDOR_IP="$(hostname -I | awk '{print $1}')"
sed -i "s|^PUBLIC_URL=.*|PUBLIC_URL=http://${SERVIDOR_IP:-localhost}|" "$DESTINO/services/orders/.env"
chown -R entradasya:entradasya "$DESTINO"
chmod 600 "$DESTINO"/services/*/.env

echo "== 5/6 systemd y Nginx =="
install -m 644 "$DESTINO/infra/systemd/entradasya@.service" /etc/systemd/system/entradasya@.service
install -m 755 "$DESTINO/infra/scripts/desplegar_servicio.sh" /usr/local/bin/entradasya-desplegar
echo "$DEPLOY_USER ALL=(root) NOPASSWD: /usr/local/bin/entradasya-desplegar" > /etc/sudoers.d/entradasya-deploy
chmod 440 /etc/sudoers.d/entradasya-deploy
visudo -cf /etc/sudoers.d/entradasya-deploy >/dev/null

systemctl daemon-reload
for s in "${SERVICIOS[@]}"; do systemctl enable --now "entradasya@$s" >/dev/null 2>&1; done

cp "$DESTINO/infra/nginx/entradasya.conf" /etc/nginx/sites-available/entradasya
ln -sf /etc/nginx/sites-available/entradasya /etc/nginx/sites-enabled/entradasya
rm -f /etc/nginx/sites-enabled/default
nginx -t && systemctl reload nginx

echo "== 6/6 Chequeos de salud =="
sleep 4
for par in web:8000 auth:8001 events:8002 orders:8003 payments:8004 tickets:8005 notifications:8006 checkin:8007; do
  s="${par%%:*}"; p="${par##*:}"
  printf "  %-14s %s\n" "$s" "$(curl -s -o /dev/null -w '%{http_code}' "http://127.0.0.1:$p/health" || true)"
done
echo
echo "Listo. Web: http://${SERVIDOR_IP:-localhost}"
echo "Los servicios arrancan solos al encender el servidor. Logs: journalctl -u entradasya@<servicio> -f"
