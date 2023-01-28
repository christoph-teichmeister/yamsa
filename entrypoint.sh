#!/bin/bash

echo "" && echo "run migrations" && echo ""
python manage.py migrate
echo "" && echo "done with migrations" && echo ""

exec "$@"
