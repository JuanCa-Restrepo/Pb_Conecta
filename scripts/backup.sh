#!/bin/sh
# Copia de seguridad de la base de datos (RNF-16). Uso: sh scripts/backup.sh
set -e
mkdir -p backups
ARCHIVO="backups/pbconecta-$(date +%Y%m%d-%H%M%S).dump"
docker compose exec -T db sh -c 'pg_dump -U "$POSTGRES_USER" -d "$POSTGRES_DB" -Fc' > "$ARCHIVO"
echo "Copia creada: $ARCHIVO"
