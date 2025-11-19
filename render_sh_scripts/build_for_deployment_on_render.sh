#!/usr/bin/env bash
# Build file for render.com

# Exit on error
set -o errexit

echo "" && echo "pip install --upgrade pip && pip install -U pip uv"
pip install --upgrade pip && pip install -U pip uv

echo "" && echo "uv export --locked --format=requirements.txt --no-dev > /tmp/requirements.txt"
uv export --locked --format=requirements.txt --no-dev --output-file /tmp/requirements.txt

echo "" && echo "pip install --no-cache-dir -r /tmp/requirements.txt"
pip install --no-cache-dir -r /tmp/requirements.txt
rm /tmp/requirements.txt

echo "" && echo "python manage.py collectstatic --no-input"
python manage.py collectstatic --no-input

echo "" && echo "python manage.py migrate"
python manage.py migrate

echo "" && echo "python manage.py deleteorphanedmedia --noinput"
# https://pypi.org/project/django-cloudinary-storage/#deleteorphanedmedia
python manage.py deleteorphanedmedia --noinput
