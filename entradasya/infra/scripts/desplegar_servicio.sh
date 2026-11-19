#!/usr/bin/env bash
# EntradasYa v1 - Despliega UN servicio en el servidor Ubuntu.
# Lo ejecuta el pipeline de cada servicio (GitHub Actions) con sudo.
# instalar_servidor.sh lo copia a /usr/local/bin/entradasya-desplegar.
#
# Uso:  sudo entradasya-desplegar <servicio> <carpeta_del_repositorio>
#
# Pasos: copia el código nuevo (sin tocar .env, .venv ni data), instala dependencias,
# reinicia el servicio con systemd y espera a que su /health responda.
set -euo pipefail

SERVICIOS="web auth events orders payments tickets notifications checkin"
DESTINO="${ENTRADASYA_DIR:-/opt/entradasya}"
USUARIO="${ENTRADASYA_USER:-entradasya}"

servicio="${1:-}"
origen="${2:-}"

if [ -z "$servicio" ] || [ -z "$origen" ]; then
  echo "Uso: $0 <servicio> <carpeta_del_repositorio>" >&2; exit 2
fi
case " $SERVICIOS " in *" $servicio "*) ;; *) echo "Servicio desconocido: $servicio" >&2; exit 2 ;; esac

src="$origen/services/$servicio"
dst="$DESTINO/services/$servicio"
[ -d "$src/app" ] || { echo "No existe $src/app" >&2; exit 2; }
[ -f "$dst/.env" ] || { echo "Falta $dst/.env: ejecute primero instalar_servidor.sh" >&2; exit 2; }

echo "==> [$servicio] Copiando código a $dst"
rsync -a --delete \
  --exclude '.env' --exclude '.venv/' --exclude 'data/' --exclude '__pycache__/' \
  "$src/" "$dst/"

echo "==> [$servicio] Instalando dependencias"
[ -x "$dst/.venv/bin/python" ] || python3 -m venv "$dst/.venv"
"$dst/.venv/bin/python" -m pip install -q --disable-pip-version-check -r "$dst/requirements.txt"
chown -R "$USUARIO:$USUARIO" "$dst"

echo "==> [$servicio] Reiniciando entradasya@$servicio"
systemctl restart "entradasya@$servicio"

puerto="$(grep -E '^PORT=' "$dst/.env" | cut -d= -f2-)"
echo "==> [$servicio] Esperando /health en el puerto $puerto"
for _ in $(seq 1 30); do
  codigo="$(curl -s -o /dev/null -w '%{http_code}' "http://127.0.0.1:$puerto/health" || true)"
  if [ "$codigo" = "200" ]; then
    echo "==> [$servicio] Desplegado correctamente (health 200)"
    exit 0
  fi
  sleep 1
done

echo "==> [$servicio] ERROR: el health no respondió 200 (último código: $codigo)" >&2
journalctl -u "entradasya@$servicio" -n 30 --no-pager >&2 || true
exit 1
