#!/bin/bash

echo "" && echo "Run migrations" && echo ""
python manage.py migrate
echo "" && echo "Done with migrations!" && echo ""

echo "" && echo "Collect static" && echo ""
python manage.py collectstatic --noinput
echo "" && echo "Done with collecting static!" && echo ""

exec "$@"
