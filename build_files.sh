#!/bin/bash

# Exit on error
set -e

echo "Building project..."

# Install dependencies
pip install -r requirements.txt

# Collect static files
python manage.py collectstatic --noinput

# Apply database migrations
python manage.py migrate --noinput

echo "Build finished."