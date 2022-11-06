#!/bin/sh
sleep 5
poetry run python manage.py collectstatic --clear --noinput
poetry run python manage.py migrate
poetry run gunicorn -b 0.0.0.0:80 Progression.wsgi:application
