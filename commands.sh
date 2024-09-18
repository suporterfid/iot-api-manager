#!/bin/bash
set -e


# makemigrations
python3 /app/manage.py makemigrations
python3 /app/manage.py migrate

# make messages
python3 /app/manage.py makemessages -l en -l pt_BR
python3 /app/manage.py compilemessages -l en -l pt_BR

# superuser
python3 /app/manage.py shell -c "from django.contrib.auth import get_user_model; \
  User = get_user_model(); User.objects.filter(username='admin').exists() \
  or User.objects.create_superuser('admin', 'admin@admin.com', 'admin')"

# collect static
python3 /app/manage.py collectstatic --noinput

# prepare entrypoint for next run
chmod +x /app/entrypoint.sh
