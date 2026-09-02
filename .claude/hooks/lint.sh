#!/bin/bash
# Runs prek over the project when Claude Code finishes a task, wired as a
# TaskCompleted hook (see settings.baseline.json).
# Linting output is sent to stderr so Claude receives it as context and can fix issues automatically.

# This hook needs BOTH the binary and a project configuration for it.
# A globally installed prek in a project that has no pre-commit config is
# not a lint-managed project — running anyway turns every completed task
# into an error. Either side missing ⇒ skip silently.
if ! command -v prek >/dev/null 2>&1; then
  exit 0
fi

PROJECT_DIR="${CLAUDE_PROJECT_DIR:-.}"
if [ ! -f "$PROJECT_DIR/.pre-commit-config.yaml" ] \
  && [ ! -f "$PROJECT_DIR/.pre-commit-config.yml" ] \
  && [ ! -f "$PROJECT_DIR/prek.toml" ]; then
  exit 0
fi

# Run Prek
OUTPUT=$(cd "$PROJECT_DIR" && SKIP=no-commit-to-branch prek run --all-files --hook-stage pre-push 2>&1)
EXIT_CODE=$?

# Return prek output to claude code
if [ $EXIT_CODE -ne 0 ]; then
  echo "prek found the following linting issues. Please fix the following errors. If you are unsure about a fix, stop and ask the user." >&2
  echo "" >&2
  echo "$OUTPUT" >&2
  exit 2
fi

exit 0
