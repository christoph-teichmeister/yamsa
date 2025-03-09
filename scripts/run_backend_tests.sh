#!/bin/bash
./manage.py collectstatic --noinput
./manage.py compilemessages
COVERAGE_CORE=sysmon pytest --cov --cov-report term --cov-report xml:coverage.xml
