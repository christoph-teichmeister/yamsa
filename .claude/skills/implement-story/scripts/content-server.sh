#!/usr/bin/env bash
# Brings up (or tears down) a throwaway smoke server for the content-review phase: its own SQLite
# database inside the run directory, seeded via create_intensive_test_data, a webpack bundle if one is
# missing, and manage.py runserver on a free port, backgrounded with no autoreload.
#
# Usage:
#   content-server.sh fresh   <run_dir> [--content-port=N]   # wipe db, migrate, seed, start
#   content-server.sh restart <run_dir> [--content-port=N]   # keep db, restart the process
#   content-server.sh start   <run_dir> [--content-port=N]   # reuse a still-answering server, else fresh
#   content-server.sh stop    <run_dir>                      # kill the process
set -uo pipefail

MODE="${1:?usage: content-server.sh <fresh|restart|start|stop> <run_dir> [--content-port=N]}"
RUN_DIR="${2:?usage: content-server.sh <fresh|restart|start|stop> <run_dir> [--content-port=N]}"
shift 2 || true

DEFAULT_PORT=8765
PORT="$DEFAULT_PORT"
for arg in "$@"; do
  case "$arg" in
    --content-port=*) PORT="${arg#--content-port=}" ;;
  esac
done

REPO_ROOT="$(git rev-parse --show-toplevel)"
cd "$REPO_ROOT" || exit 1

CONTENT_DIR="$RUN_DIR/content"
mkdir -p "$CONTENT_DIR"
DB_PATH="$CONTENT_DIR/smoke.sqlite3"
PID_FILE="$CONTENT_DIR/.pid"
PORT_FILE="$CONTENT_DIR/.port"
LOG_FILE="$CONTENT_DIR/server.log"
SETUP_LOG="$CONTENT_DIR/setup.log"

export DJANGO_DATABASE_URL="sqlite:///$DB_PATH"
export DJANGO_DEBUG=True
export DJANGO_SECRET_KEY="${DJANGO_SECRET_KEY:-smoke-server-secret-key}"
export DJANGO_SESSION_COOKIE_SECURE=False
export DJANGO_ALLOWED_HOSTS="127.0.0.1,localhost"

is_up() {
  [ -f "$PID_FILE" ] && kill -0 "$(cat "$PID_FILE")" 2>/dev/null
}

stop_server() {
  if is_up; then
    kill "$(cat "$PID_FILE")" 2>/dev/null
    for _ in $(seq 1 20); do
      kill -0 "$(cat "$PID_FILE")" 2>/dev/null || break
      sleep 0.2
    done
    kill -9 "$(cat "$PID_FILE")" 2>/dev/null || true
  fi
  rm -f "$PID_FILE"
}

free_port() {
  local p="$PORT"
  while python3 -c "import socket,sys; s=socket.socket(); sys.exit(0 if s.connect_ex(('127.0.0.1', $p))==0 else 1)"; do
    p=$((p + 1))
  done
  echo "$p"
}

ensure_bundle() {
  if [ ! -f webpack_bundles/bundles/webpack-stats.json ]; then
    [ -d node_modules ] || { echo "node_modules missing - run 'yarn install' first" | tee -a "$SETUP_LOG"; exit 1; }
    echo "building webpack bundle..." | tee -a "$SETUP_LOG"
    yarn build >>"$SETUP_LOG" 2>&1 || { echo "yarn build failed - see $SETUP_LOG"; exit 1; }
  fi
}

start_server() {
  ensure_bundle
  PORT="$(free_port)"
  echo "$PORT" >"$PORT_FILE"
  nohup uv run python manage.py runserver --noreload "127.0.0.1:$PORT" >"$LOG_FILE" 2>&1 &
  echo $! >"$PID_FILE"
  for _ in $(seq 1 30); do
    curl -sf "http://127.0.0.1:$PORT/account/login/" >/dev/null 2>&1 && break
    sleep 0.3
  done
  echo "smoke server: http://127.0.0.1:$PORT/"
  echo "login: registered_user_1@yamsa.local / Admin123\$  (admin: admin@yamsa.local, same password)"
  echo "log: $LOG_FILE"
}

case "$MODE" in
  fresh)
    stop_server
    rm -f "$DB_PATH"
    echo "migrating..." | tee "$SETUP_LOG"
    uv run python manage.py migrate >>"$SETUP_LOG" 2>&1 || { echo "migrate failed - see $SETUP_LOG"; exit 1; }
    echo "seeding..." | tee -a "$SETUP_LOG"
    uv run python manage.py create_intensive_test_data --force >>"$SETUP_LOG" 2>&1 \
      || { echo "seed failed - see $SETUP_LOG"; exit 1; }
    start_server
    ;;
  restart)
    stop_server
    start_server
    ;;
  start)
    if is_up; then
      PORT="$(cat "$PORT_FILE" 2>/dev/null || echo "$DEFAULT_PORT")"
      echo "reusing running smoke server: http://127.0.0.1:$PORT/"
    else
      if [ -f "$DB_PATH" ]; then
        start_server
      else
        exec "$0" fresh "$RUN_DIR" "--content-port=$PORT"
      fi
    fi
    ;;
  stop)
    stop_server
    echo "smoke server stopped"
    ;;
  *)
    echo "unknown mode: $MODE" >&2
    exit 1
    ;;
esac
