#!/bin/bash
python manage.py migrate
# python manage.py collectstatic

daphne -b 0.0.0.0 -p 8000 envirol.asgi:application
