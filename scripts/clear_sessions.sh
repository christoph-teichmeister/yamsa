#!/bin/bash
echo Clear django sessions
./manage.py clearsessions

echo Clear axes logs
./manage.py axes_reset_logs
