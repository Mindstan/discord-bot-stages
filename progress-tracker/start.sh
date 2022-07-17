#!/bin/sh
sleep 5
python3 manage.py collectstatic --clear --noinput
python3 manage.py migrate
gunicorn -b 0.0.0.0:80 Progression.wsgi:application
