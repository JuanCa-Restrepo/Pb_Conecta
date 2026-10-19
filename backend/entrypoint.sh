#!/bin/sh
# Prepara la base de datos antes de arrancar el proceso principal del contenedor.
set -e

if [ "$EJECUTAR_MIGRACIONES" = "1" ]; then
    echo "[entrypoint] Aplicando migraciones..."
    python manage.py migrate --noinput

    if [ "$CARGAR_DEMO" = "1" ]; then
        python manage.py cargar_demo
    fi

    if [ "$DJANGO_DEBUG" = "0" ]; then
        python manage.py collectstatic --noinput
    fi
fi

exec "$@"
