# Set Python
ARG PYTHON_MINOR_VERSION=3.11

# Set global variable to export path from "builder-python" in production image
ARG ENV_PATH

#ARG UID=1000
#ARG GID=1000

### STAGE 1: Build python ###
FROM python:${PYTHON_MINOR_VERSION} AS builder-python

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set work directory
ENV TMP_DIR=/tmp/
WORKDIR $TMP_DIR

# Install OS dependencies required for the build
RUN apt-get update && \
    apt-get install -y && \
    apt-get upgrade -y && \
    apt-get clean

# Move pipfiles to project
COPY Pipfile Pipfile.lock $TMP_DIR
RUN pip install -U pip pipenv
RUN pipenv install --system --deploy --dev

# Set Path variable to global arg var
ARG ENV_PATH
RUN ENV_PATH=$PATH

### STAGE 2: Setup ###
FROM python:${PYTHON_MINOR_VERSION}-slim AS production

# Declare global variable to make it accessible
ARG PYTHON_MINOR_VERSION
ARG ENV_PATH
ARG UID
ARG GID

# Install required OS dependencies
# We have to have "gettext" here as well to be able to run "makemigrations"
RUN apt-get update && \
    apt-get install && \
    apt-get clean

# Extend system PATH variable with path from python builder which is required for all python binaries like celery
ENV PATH="$ENV_PATH:${PATH}"

# Directory in container for project source files
ENV PROJECT_HOME=/yamsa

# Create application subdirectories
WORKDIR $PROJECT_HOME

#ENV USER_NAME=yamsa_docker_user
#ENV USER_GROUP=$USER_NAME

# Create and set user and group
#RUN groupadd -r -g "${GID}" $USER_GROUP && useradd -g "${GID}" -u "${UID}" --home $PROJECT_HOME $USER_NAME

# Switch user
#USER $USER_NAME

# Copy python executables
#COPY --chown=$USER_NAME:$USER_GROUP --from=builder-python /usr/local/lib/python${PYTHON_MINOR_VERSION}/site-packages/ /usr/local/lib/python${PYTHON_MINOR_VERSION}/site-packages/
COPY --from=builder-python /usr/local/lib/python${PYTHON_MINOR_VERSION}/site-packages/ /usr/local/lib/python${PYTHON_MINOR_VERSION}/site-packages/
# Copy python binaries
#COPY --chown=$USER_NAME:$USER_GROUP --from=builder-python /usr/local/bin/ /usr/local/bin/
COPY --from=builder-python /usr/local/bin/ /usr/local/bin/

# Copy application source code to project home
#COPY --chown=$USER_NAME:$USER_GROUP . $PROJECT_HOME
COPY  . $PROJECT_HOME

# Create empty env-file to avoid warnings
RUN touch $PROJECT_HOME/apps/config/.env

# EXPOSE port 8000 to allow communication to/from server
EXPOSE 8000

# Make entrypoint.sh executable
RUN ["chmod", "+x", "./entrypoint.sh"]

# Run entry point script
ENTRYPOINT ["sh", "./entrypoint.sh"]

# TODO CT: What to do with this...
# Passes runserver to entrypoint
CMD python manage.py runserver 0.0.0.0:8000
