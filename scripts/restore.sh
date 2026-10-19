#!/bin/sh
# Restaura una copia de seguridad (RNF-16). Uso: sh scripts/restore.sh backups/pbconecta-AAAAMMDD-HHMMSS.dump
# ATENCIÓN: reemplaza los datos actuales de la base de datos.
set -e
if [ -z "$1" ] || [ ! -f "$1" ]; then
  echo "Uso: sh scripts/restore.sh <archivo.dump>"
  exit 1
fi
docker compose exec -T db sh -c 'pg_restore -U "$POSTGRES_USER" -d "$POSTGRES_DB" --clean --if-exists --no-owner' < "$1"
echo "Restauración completada desde $1"
