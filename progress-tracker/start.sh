#!/bin/sh
python3 manage.py collectstatic
gunicorn -b 0.0.0.0:80 Progression.wsgi:application
