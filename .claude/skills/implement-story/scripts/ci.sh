#!/usr/bin/env bash
# Runs this project's actual local CI gates and writes ci.md + ci-logs/ into the given run directory.
#
# Usage: ci.sh <run_dir>
set -uo pipefail

RUN_DIR="${1:?usage: ci.sh <run_dir>}"
LOG_DIR="$RUN_DIR/ci-logs"
mkdir -p "$LOG_DIR"

pass=1
summary=""

run_gate() {
  local name="$1" log="$LOG_DIR/$2"
  shift 2
  if "$@" >"$log" 2>&1; then
    summary+="- ✅ $name\n"
  else
    summary+="- ❌ $name (see ci-logs/$(basename "$log"))\n"
    pass=0
  fi
}

# pre-commit twice: ruff-format/djlint rewrite files on the first pass, so only the second pass
# can confirm the tree is actually clean.
pre-commit run --all-files >"$LOG_DIR/pre-commit-1.log" 2>&1
run_gate "pre-commit (2nd pass, tree clean)" "pre-commit-2.log" pre-commit run --all-files

run_gate "pytest (coverage)" "pytest.log" bash -c "uv run coverage run -m pytest && uv run coverage report"

run_gate "migration leaf conflicts" "migrations.log" \
  bash "$(dirname "${BASH_SOURCE[0]}")/migration-numbers.sh" "$RUN_DIR"

{
  echo "# CI gates"
  echo
  echo -e "$summary"
} >"$RUN_DIR/ci.md"

cat "$RUN_DIR/ci.md"
[ "$pass" -eq 1 ]
