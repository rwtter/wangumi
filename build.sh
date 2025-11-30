#!/usr/bin/env bash
set -e

echo "Installing frontend dependencies and building production assets..."
pushd frontend > /dev/null
npm install
npm run build
popd > /dev/null

echo "Installing backend dependencies and collecting static files..."
pip install -r requirements.txt
python backend/manage.py collectstatic --noinput

echo "Applying database migrations..."
python backend/manage.py migrate
