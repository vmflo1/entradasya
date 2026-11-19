#!/usr/bin/env bash
# EntradasYa v1 - Preparación en Linux/Ubuntu.
#  1) Crea el .env de cada servicio (contraseñas y secretos aleatorios)
#  2) Crea las bases de datos y usuarios en PostgreSQL
#  3) Crea el entorno virtual de cada servicio e instala sus dependencias
#
# Uso:  bash scripts/setup.sh
# Variables opcionales: PYTHON (python3), PSQL_CMD ("sudo -u postgres psql")
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PYTHON="${PYTHON:-python3}"
PSQL_CMD="${PSQL_CMD:-sudo -u postgres psql}"
SERVICIOS=(web auth events orders payments tickets notifications checkin)
CON_BD=(auth events orders payments tickets checkin)

gen() { "$PYTHON" -c "import secrets,string;a=string.ascii_letters+string.digits;print(''.join(secrets.choice(a) for _ in range($1)))"; }
leer() { if [ -f "$1" ]; then grep -E "^$2=" "$1" | head -n1 | cut -d= -f2- || true; fi; }

echo "== 1/3 Archivos .env =="
JWT="$(leer "$ROOT/services/auth/.env" JWT_SECRET)"
if [ -z "$JWT" ] || [ "$JWT" = "cambiar_secreto_jwt" ]; then JWT="$(gen 48)"; fi
KEY="$(leer "$ROOT/services/orders/.env" INTERNAL_API_KEY)"
if [ -z "$KEY" ] || [ "$KEY" = "cambiar_clave_interna" ]; then KEY="$(gen 32)"; fi

declare -A PASS
for s in "${CON_BD[@]}"; do
  p="$(leer "$ROOT/services/$s/.env" DB_PASSWORD)"
  if [ -z "$p" ] || [ "$p" = "cambiar_password" ]; then p="$(gen 20)"; fi
  PASS[$s]="$p"
done

completar() {  # rellena los valores de ejemplo con los secretos generados
  sed -e "s|cambiar_password|${PASS[$1]:-}|" -e "s|cambiar_secreto_jwt|$JWT|" -e "s|cambiar_clave_interna|$KEY|"
}

for s in "${SERVICIOS[@]}"; do
  envf="$ROOT/services/$s/.env"
  ejemplo="$ROOT/services/$s/.env.example"
  if [ ! -f "$envf" ]; then
    completar "$s" < "$ejemplo" > "$envf"
    echo "   $s/.env creado"
    continue
  fi
  # Ya existe: se conserva y solo se agregan las variables nuevas que falten
  agregadas=0
  while IFS= read -r linea; do
    case "$linea" in ''|'#'*) continue ;; esac
    clave="${linea%%=*}"
    if ! grep -qE "^${clave}=" "$envf"; then
      [ $agregadas -eq 0 ] && printf "\n# Variables agregadas por setup.sh\n" >> "$envf"
      printf "%s\n" "$linea" | completar "$s" >> "$envf"
      agregadas=$((agregadas + 1))
    fi
  done < "$ejemplo"
  echo "   $s/.env ya existe (se conserva, $agregadas variables nuevas)"
done

echo "== 2/3 Bases de datos =="
$PSQL_CMD -q \
  -v auth_pass="${PASS[auth]}" -v events_pass="${PASS[events]}" -v orders_pass="${PASS[orders]}" \
  -v payments_pass="${PASS[payments]}" -v tickets_pass="${PASS[tickets]}" -v checkin_pass="${PASS[checkin]}" \
  < "$ROOT/infra/postgres/01_crear_bases.sql"
echo "   Bases y usuarios listos"

echo "== 3/3 Entornos virtuales y dependencias =="
for s in "${SERVICIOS[@]}"; do
  dir="$ROOT/services/$s"
  [ -d "$dir/.venv" ] || "$PYTHON" -m venv "$dir/.venv"
  "$dir/.venv/bin/python" -m pip install -q --disable-pip-version-check -r "$dir/requirements.txt"
  echo "   $s listo"
done

echo
echo "Preparación terminada. Inicie todo con: bash scripts/start.sh"
