#!/usr/bin/env bash
# Build file for render.com

# Exit on error
set -o errexit

echo "" && echo "pip install --upgrade pip && pip install -U pip pipenv"
pip install --upgrade pip && pip install -U pip pipenv

echo "" && echo "pipenv install --system --deploy"
pipenv install --system --deploy

echo "" && echo "python manage.py collectstatic --noinput"
python manage.py collectstatic --no-input

echo "" && echo "python manage.py migrate"
python manage.py migrate

echo "" && echo "python manage.py deleteorphanedmedia --noinput"
# https://pypi.org/project/django-cloudinary-storage/#deleteorphanedmedia
python manage.py deleteorphanedmedia --noinput
