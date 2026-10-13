#!/usr/bin/env bash
# Devuelve el entorno al estado inicial: borra contenedores y volúmenes (incluida Caja Sur)
# y levanta de nuevo las cajas simuladas y su servicio. No modifica su código ni su .env.
set -euo pipefail
cd "$(dirname "$0")"
docker compose --profile "*" down -v --remove-orphans
[ -f .env ] || cp .env.example .env
docker compose up -d --build
docker compose ps
