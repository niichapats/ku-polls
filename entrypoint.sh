#!/bin/sh
python ./manage.py migrate
python ./manage.py runserver 0.0.0.0:8000

gunicorn mysite.wsgi:application --bind 0.0.0.0:8000
