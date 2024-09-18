#!/bin/sh
echo "Running Gunicorn"
exec gunicorn --workers 3 --bind 0.0.0.0:8000 config.wsgi:application