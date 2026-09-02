#!/bin/bash
# stdin is the hook payload: { tool_name, tool_input: { skill, args }, session_id, ... }
# matcher already filtered to Skill, so no tool_name check needed

payload=$(cat)
skill=$(jq -r '.tool_input.skill' <<< "$payload")
args=$(jq -r '.tool_input.args // ""' <<< "$payload")

mkdir -p "${CLAUDE_PROJECT_DIR:-.}/.claude"
echo "$(date -u +%s)  $USER   $skill  $args" >> "${CLAUDE_PROJECT_DIR:-.}/.claude/skill-usage.log"
