# Set Python version
ARG PYTHON_MINOR_VERSION=3.11

### STAGE 1: Build python ###
FROM python:${PYTHON_MINOR_VERSION} AS builder-python

# Can be used to install dev dependencies (e.g. for local development in Docker):
ARG UV_EXPORT_ARGS=""

# Set work directory
WORKDIR /tmp/

# Move project metadata to build context
COPY pyproject.toml uv.lock /tmp/
RUN pip install -U pip uv
RUN uv export --locked --format=requirements.txt --no-hashes --no-emit-project ${UV_EXPORT_ARGS} > /tmp/requirements.txt && \
    pip install --no-cache-dir -r /tmp/requirements.txt && \
    rm /tmp/requirements.txt

### STAGE 2: Setup ###
FROM python:${PYTHON_MINOR_VERSION}-slim AS production

# Declare global variable to make it accessible
ARG PYTHON_MINOR_VERSION

# Install required OS dependencies
# We have to have "gettext" here as well to be able to run "makemigrations"
RUN apt-get update && \
    apt-get install --no-install-recommends -y \
      # https://github.com/Kozea/WeasyPrint/issues/2011#issuecomment-2129234529
      weasyprint \
      # Translations dependencies:
      gettext \
      locales && \
    sed -i -e "s/# en_GB.UTF-8.*/en_GB.UTF-8 UTF-8/" /etc/locale.gen && \
    sed -i -e "s/# de_DE.UTF-8.*/de_DE.UTF-8 UTF-8/" /etc/locale.gen && \
    locale-gen de_DE.UTF-8 \
    update-locale LANG=de_DE.UTF-8 && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Directory in container for project source files
ENV PROJECT_HOME=/src

# Declare locales
ENV LANG de_DE.UTF-8
ENV LANGUAGE de_DE:de
ENV LC_ALL de_DE.UTF-8
ENV PYTHONUNBUFFERED 1

# Create and set user and group
RUN groupadd --gid 2000 web && useradd -u 1000 -g web -m --home-dir "$PROJECT_HOME" web

# Switch user
USER web

# Copy python executables
COPY --chown=web:web --from=builder-python /usr/local/lib/python${PYTHON_MINOR_VERSION}/site-packages/ /usr/local/lib/python${PYTHON_MINOR_VERSION}/site-packages/
# Copy python binaries
COPY --chown=web:web --from=builder-python /usr/local/bin/ /usr/local/bin/

# Create application subdirectories
WORKDIR $PROJECT_HOME

# Copy application source code to project home
COPY --chown=web:web . $PROJECT_HOME

# Create empty env-file to avoid warnings by django
RUN touch "$PROJECT_HOME/apps/config/.env"
RUN touch "$PROJECT_HOME/apps/config/development.env"

# Run collectstatic for whitenoise
RUN #python ./manage.py collectstatic --noinput

# Compile translated messages
RUN #python ./manage.py compilemessages

# EXPOSE port 8000 to allow communication to/from server
EXPOSE 8000

CMD ["./scripts/run_backend.sh"]
