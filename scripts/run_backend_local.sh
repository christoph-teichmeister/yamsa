#!/bin/bash

echo "Applying database migrations" && echo ""
bash ./scripts/run_migrations.sh
echo "" && echo "Database migrations done." && echo ""

echo "Applying fixtures" && echo ""
bash ./scripts/apply_fixtures.sh
echo "" && echo "Applying fixtures done." && echo ""

echo "Starting django server (runserver) on 0.0.0.0:8000" && echo ""
python manage.py runserver 0.0.0.0:8000
