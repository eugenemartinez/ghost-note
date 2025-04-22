#!/bin/bash

# Exit on error
set -e

echo "Running build commands..."

# pip install -r requirements.txt # No longer needed here, @vercel/python does this

# Collect static files (add --clear for cleaner builds)
python manage.py collectstatic --noinput --clear

# Apply database migrations
python manage.py migrate --noinput

echo "Build commands finished."