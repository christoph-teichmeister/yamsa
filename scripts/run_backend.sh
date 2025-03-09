#!/bin/bash

echo Starting uvicorn.
# Be aware, as of August 2024, uvicorn only seem to support maximum of 4kb header size for clients with no option to adjust.
# If you expect to have relatively big header size, uvicorn may not be suitable option. Consider switching to gunicorn in such case.
# gunicorn have 8kb of client header size limit by default with option to adjust it as needed.
# You can expect to have large client header size especially if you integrate SSO into your project.
# uvicorn header limit issue: https://github.com/encode/uvicorn/discussions/1669
exec uvicorn --host 0.0.0.0 --port 8000 apps.config.asgi:application
