#!/bin/sh
set -eu
python -m flask --app wsgi init-db
exec gunicorn --bind "0.0.0.0:${PORT:-8000}" --workers 2 --timeout 60 --access-logfile - --error-logfile - wsgi:app
