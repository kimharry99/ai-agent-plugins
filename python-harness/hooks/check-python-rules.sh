#!/usr/bin/env bash
# Guardrail hook: checks Python files for banned patterns on file write.
# Receives PostToolUse JSON on stdin.
#
# Coverage: Write/Edit tools and Codex apply_patch aliases.
# MCP and other third-party tools that modify Python files are NOT caught here;
# they are covered indirectly via the rule-reminder SessionStart hook.

set -euo pipefail

command -v jq >/dev/null 2>&1 || exit 0
command -v python3 >/dev/null 2>&1 || exit 0

INPUT=$(cat)
FILES=$(echo "$INPUT" | jq -r '
[
    .tool_input.file_path?,
    .tool_response.filePath?,
    (
        .tool_input.command?
        | strings
        | split("\n")[]
        | (
            try capture("^\\*\\*\\* (?:Add File|Update File|Move to): (?<path>.+)$").path
            catch empty
        )
    ),
    (
        .tool_input.patch?
        | strings
        | split("\n")[]
        | (
            try capture("^\\*\\*\\* (?:Add File|Update File|Move to): (?<path>.+)$").path
            catch empty
        )
    ),
    (
        .tool_input
        | strings
        | split("\n")[]
        | (
            try capture("^\\*\\*\\* (?:Add File|Update File|Move to): (?<path>.+)$").path
            catch empty
        )
    )
]
| map(select(. != null and endswith(".py")))
| unique
| .[]
')

ERRORS=""

while IFS= read -r FILE; do
    [[ "$FILE" == *.py ]] || continue
    [[ -f "$FILE" ]] || continue

    BANNED=$(grep -nE '\b(setattr|getattr|hasattr)\s*\(' "$FILE" 2>/dev/null || true)
    if [[ -n "$BANNED" ]]; then
        ERRORS+="$FILE: banned builtin usage (setattr/getattr/hasattr):\n$BANNED\n\n"
    fi

    IS_TEST=false
    [[ "$FILE" == *test_* || "$FILE" == *_test.py || "$FILE" == */tests/* || "$FILE" == */test/* ]] && IS_TEST=true
    if [[ "$IS_TEST" == false ]]; then
        INLINE=$(python3 - "$FILE" <<'PYEOF' 2>/dev/null || true
import ast, sys

with open(sys.argv[1]) as f:
    tree = ast.parse(f.read())

for node in ast.walk(tree):
    for child in ast.iter_child_nodes(node):
        if isinstance(child, (ast.Import, ast.ImportFrom)):
            if not isinstance(node, ast.Module):
                mod = ''
                if isinstance(child, ast.ImportFrom):
                    mod = child.module or ''
                names = ', '.join(a.name for a in child.names)
                print(f'  line {child.lineno}: import {mod} {names}'.strip())
PYEOF
)

        if [[ -n "$INLINE" ]]; then
            ERRORS+="$FILE: inline imports detected (must be at top of file):\n$INLINE\n"
        fi
    fi
done <<< "$FILES"

if [[ -n "$ERRORS" ]]; then
    REASON=$(echo -e "$ERRORS" | head -20)
    jq -n --arg reason "$REASON" '{
        "decision": "block",
        "reason": $reason
    }'
    exit 0
fi
