#!/usr/bin/env bash
# build.sh — Render Build Script for RestSureAI
# Render runs this automatically on every deploy.

set -o errexit  # Exit on any error

echo ">>> Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

echo ">>> Collecting static files (WhiteNoise)..."
python manage.py collectstatic --noinput

echo ">>> Running database migrations (Neon PostgreSQL)..."
python manage.py migrate --noinput

echo ">>> Building Matplotlib font cache..."
python -c "import matplotlib.pyplot"

echo ">>> Build complete!"
