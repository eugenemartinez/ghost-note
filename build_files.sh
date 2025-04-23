#!/bin/bash

# set -e # Temporarily remove exit on error to see more logs

echo "--- build_files.sh starting ---"

echo "--- Running collectstatic ---"
python manage.py collectstatic --noinput --clear || echo "!!! collectstatic failed !!!"

echo "--- Running migrate ---"
python manage.py migrate --noinput || echo "!!! migrate failed !!!"

echo "--- build_files.sh finished ---"