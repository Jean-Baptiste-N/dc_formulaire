#!/bin/sh
set -e

echo "==> Creating migrations..."
python manage.py makemigrations

echo "==> Applying database migrations..."
python manage.py migrate --noinput

echo "==> Collecting static files..."
rm -rf /app/staticfiles
python manage.py collectstatic --noinput

echo "==> Starting server..."
exec "$@"
