#!/usr/bin/env bash
# Exit on error
set -o errexit

echo ">>> Installing dependencies..."
pip install -r requirements.txt

echo ">>> Collecting static files..."
python manage.py collectstatic --noinput

echo ">>> Running database migrations..."
python manage.py migrate

echo ">>> Seeding initial data..."
python seed_se_articles.py || echo "Warning: Seeding script skipped or failed, continuing..."

echo ">>> Build completed successfully!"
