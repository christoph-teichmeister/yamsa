#!/bin/bash

# WSGI via gunicorn: the app has no async views or websockets, and gunicorn's client header limit is adjustable
# (uvicorn caps at 4kb, too small once SSO/passkey cookies pile up: https://github.com/encode/uvicorn/discussions/1669).
exec gunicorn --bind 0.0.0.0:8000 apps.config.wsgi:application
