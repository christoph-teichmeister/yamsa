---
description: Run prek on all files and fix reported issues
---

Run the project's lint script via Bash:

```
"${CLAUDE_PROJECT_DIR:-.}/.claude/hooks/lint.sh"
```

- Exit 0 with no output: everything clean (or prek is not installed in this
  project — say which of the two it was, `command -v prek` tells you).
- Non-zero exit: fix the reported issues, then re-run the script until it
  passes. If you are unsure about a fix, stop and ask the user.
