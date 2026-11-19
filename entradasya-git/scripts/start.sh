#!/usr/bin/env bash
# EntradasYa v1 - Inicia los 8 servicios en segundo plano (Linux).
# Logs en logs/<servicio>.log. Para detenerlos: bash scripts/stop.sh
# Nginx y Mailpit se instalan aparte (ver README).
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SERVICIOS=(auth events payments tickets notifications orders checkin web)
mkdir -p "$ROOT/logs" "$ROOT/run"

for s in "${SERVICIOS[@]}"; do
  pidf="$ROOT/run/$s.pid"
  if [ -f "$pidf" ] && kill -0 "$(cat "$pidf")" 2>/dev/null; then
    echo "$s ya está en ejecución (pid $(cat "$pidf"))"
    continue
  fi
  cd "$ROOT/services/$s"
  nohup .venv/bin/python -m app.main > "$ROOT/logs/$s.log" 2>&1 &
  echo $! > "$pidf"
  cd "$ROOT"
  echo "$s iniciado (pid $(cat "$pidf"))"
done

echo
echo "Chequeos de salud (esperando a que respondan):"
for par in web:8000 auth:8001 events:8002 orders:8003 payments:8004 tickets:8005 notifications:8006 checkin:8007; do
  s="${par%%:*}"; p="${par##*:}"; estado="000"
  for _ in $(seq 1 20); do
    estado="$(curl -s -o /dev/null -w '%{http_code}' "http://127.0.0.1:$p/health" || true)"
    [ "$estado" != "000" ] && break
    sleep 0.75
  done
  echo "  $s ($p): $estado"
done
echo
WEB_URL="$(grep -E '^PUBLIC_URL=' "$ROOT/services/orders/.env" 2>/dev/null | cut -d= -f2-)"
echo "Web (a través de Nginx): ${WEB_URL:-http://localhost}   ·   Correos (Mailpit): http://localhost:8025"
