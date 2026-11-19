#!/usr/bin/env bash
# EntradasYa v1 - Detiene los servicios iniciados con start.sh (Linux).
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
for pidf in "$ROOT"/run/*.pid; do
  [ -f "$pidf" ] || continue
  s="$(basename "$pidf" .pid)"
  if kill "$(cat "$pidf")" 2>/dev/null; then echo "$s detenido"; fi
  rm -f "$pidf"
done
