#!/bin/bash
echo "clear django sessions"
./manage.py clearsessions

echo "clear axes logs"
./manage.py axes_reset_logs
