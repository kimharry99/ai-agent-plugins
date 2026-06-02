#!/usr/bin/env bash
# Build a unified diff for code-review scope. Prints DIFF_PATH / MODE / BASE to stdout.
# Exit codes: 0 = diff produced, 2 = nothing to review, 1 = error.
set -euo pipefail

mode="auto"
base=""
pathspecs=()

while [[ $# -gt 0 ]]; do
    case "$1" in
        --mode) mode="$2"; shift 2 ;;
        --base) base="$2"; shift 2 ;;
        --) shift; pathspecs+=("$@"); break ;;
        *) echo "unknown arg: $1" >&2; exit 1 ;;
    esac
done

if ! git rev-parse --git-dir >/dev/null 2>&1; then
    echo "not inside a git repository" >&2
    exit 1
fi

repo_root=$(git rev-parse --show-toplevel)
tmp_dir="${repo_root}/.claude/tmp"
mkdir -p "$tmp_dir"
out="${tmp_dir}/code-review-$(date +%s).diff"

resolve_base() {
    if [[ -n "$base" ]]; then
        git rev-parse --verify "$base" >/dev/null 2>&1 || { echo "base ref not found: $base" >&2; exit 1; }
        echo "$base"; return
    fi
    local upstream
    if upstream=$(git rev-parse --abbrev-ref '@{u}' 2>/dev/null); then
        local head_branch
        head_branch=$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo "")
        if [[ "$upstream" != "$head_branch" && -n "$upstream" ]]; then
            echo "$upstream"; return
        fi
    fi
    local origin_head
    if origin_head=$(git symbolic-ref --quiet refs/remotes/origin/HEAD 2>/dev/null); then
        echo "${origin_head#refs/remotes/}"; return
    fi
    for cand in origin/main origin/master main master; do
        if git rev-parse --verify "$cand" >/dev/null 2>&1; then
            echo "$cand"; return
        fi
    done
    echo "could not resolve a base branch; pass --base <ref>" >&2
    exit 1
}

working_dirty() {
    ! git diff --quiet HEAD -- "${pathspecs[@]}" 2>/dev/null \
        || ! git diff --cached --quiet -- "${pathspecs[@]}" 2>/dev/null \
        || has_untracked_files
}

has_untracked_files() {
    local file
    while IFS= read -r -d '' file; do
        return 0
    done < <(git ls-files --others --exclude-standard -z -- "${pathspecs[@]}" ':!.claude/tmp/**')
    return 1
}

write_untracked_diff() {
    local file
    while IFS= read -r -d '' file; do
        git diff --no-index --no-color -- /dev/null "$file" >> "$out" 2>/dev/null || true
    done < <(git ls-files --others --exclude-standard -z -- "${pathspecs[@]}" ':!.claude/tmp/**')
}

write_working_diff() {
    {
        git diff --cached -- "${pathspecs[@]}" 2>/dev/null || true
        git diff -- "${pathspecs[@]}" 2>/dev/null || true
    } >> "$out"
    write_untracked_diff
}

write_branch_diff() {
    local b="$1"
    local mb
    mb=$(git merge-base "$b" HEAD 2>/dev/null) || { echo "no merge base with $b" >&2; exit 1; }
    git diff "${mb}..HEAD" -- "${pathspecs[@]}" >> "$out"
    if working_dirty; then
        write_working_diff
    fi
}

: > "$out"

resolved_base=""
case "$mode" in
    working)
        write_working_diff
        ;;
    branch)
        resolved_base=$(resolve_base)
        write_branch_diff "$resolved_base"
        ;;
    auto)
        resolved_base=$(resolve_base)
        head_sha=$(git rev-parse HEAD)
        base_sha=$(git rev-parse "$resolved_base")
        if [[ "$head_sha" == "$base_sha" ]]; then
            if working_dirty; then
                mode="working"
                write_working_diff
                resolved_base=""
            else
                rm -f "$out"
                echo "nothing to review" >&2
                exit 2
            fi
        else
            mode="branch"
            write_branch_diff "$resolved_base"
        fi
        ;;
    *)
        echo "invalid mode: $mode" >&2; exit 1 ;;
esac

if [[ ! -s "$out" ]]; then
    rm -f "$out"
    echo "nothing to review" >&2
    exit 2
fi

echo "DIFF_PATH=$out"
echo "MODE=$mode"
if [[ "$mode" == "branch" && -n "$resolved_base" ]]; then
    echo "BASE=$resolved_base"
fi
