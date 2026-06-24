#!/bin/sh
set -e

echo "==> Applying database migrations..."
python manage.py migrate --noinput

echo "==> Collecting static files..."
rm -rf /app/staticfiles
python manage.py collectstatic --noinput --clear

echo "==> Starting server..."
exec "$@"
