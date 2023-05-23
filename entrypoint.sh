#!/bin/bash

echo "" && echo "Run migrations" && echo ""
python manage.py migrate
echo "" && echo "Done with migrations!" && echo ""

exec "$@"
