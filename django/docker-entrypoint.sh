#!/bin/sh

echo "Performing Django database migrations (if any)"
python manage.py migrate --no-input

# Creat a super user
python manage.py shell -c 'from scripts import createsuperuser; createsuperuser.run()'

echo "Ensuring model history tracking is enabled"
python manage.py triggers enable

echo "Copying static files"
python manage.py collectstatic --no-input --clear

# Execute the CMD from the Dockerfile:
exec "$@"
