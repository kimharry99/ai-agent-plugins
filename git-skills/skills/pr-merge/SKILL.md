---
name: pr-merge
description: 'Full PR merge workflow — rebases the current branch onto its target (defaults to main), force-pushes, verifies unresolved review threads have replies and resolves them, verifies the Test Plan, re-checks for new unresolved threads, and merges via a merge commit. Use when the user says: (1) "merge PR", (2) "rebase and merge", (3) "land this PR", or (4) "/pr-merge".'
---

# pr-merge

## Pre-flight: gather context

Collect the following in parallel:

- `<BRANCH>`: `git branch --show-current`
- `<TARGET>`: user-specified, default `main`
- `<PR_NUMBER>`: user-specified, or `gh pr view --json number -q .number`

If `<BRANCH>` equals `<TARGET>` (already on the target branch), stop and tell the user.

If `<PR_NUMBER>` cannot be determined automatically, ask the user before proceeding.

## Tool discovery

At runtime, scan the available tool list for tools matching these patterns (glob — match any tool whose name contains the listed string):

| Operation | MCP pattern | gh CLI fallback |
|---|---|---|
| Merge PR | `*merge_pull_request*` | `gh pr merge` |
| Fetch PR details (body) | `*get_pull_request*` | `gh pr view --json body` |
| Update PR body | `*update_pull_request*` | `gh pr edit --body-file` |
| List review threads (with resolution status) | `*list_pull_request_review_threads*` or `*get_review_threads*` | `gh api graphql` (see Step 4) |
| Resolve a review thread | `*resolve_review_thread*` | `gh api graphql` (see Step 5) |
| Identify current user | `*get_authenticated_user*` or `*viewer*` | `gh api user -q .login` |

Use the first match for each. If no MCP tool matches, fall back to the gh CLI. If neither an MCP tool nor the `gh` CLI is available, stop immediately and tell the user that GitHub access is required to run this skill.

Thread resolution has no REST or `gh` subcommand — `gh api graphql` is the only fallback. Resolve `{owner}` and `{repo}` for GraphQL calls by parsing `git remote get-url origin`.

**Merge tool verification:** Before using the discovered `*merge_pull_request*` tool, confirm it accepts a `merge_method` parameter (or equivalent). If it does not, fall back to `gh pr merge --merge`. Using a tool without `merge_method` control risks a silent squash or rebase-fast-forward merge.

## Workflow

### Step 1 — fetch latest remote state

```bash
git fetch origin
```

### Step 2 — rebase onto target

```bash
git rebase origin/<TARGET>
```

**CRITICAL: if the rebase exits with a non-zero code, or its output contains the word `CONFLICT`, STOP IMMEDIATELY.**

Output the following message to the user and do nothing else:

```
Rebase conflict detected. Please resolve conflicts manually:

1. Edit the conflicting files shown above.
2. Stage the resolved files: git add <resolved-files>
3. Continue the rebase: git rebase --continue
4. Once the rebase completes cleanly, invoke /pr-merge again.

Do NOT run `git rebase --abort` unless you want to discard the rebase entirely.
```

Do NOT attempt to auto-resolve any conflict. Do NOT proceed further.

### Step 3 — push with force-with-lease

After a clean rebase (no conflicts):

```bash
git push --force-with-lease origin <BRANCH>
```

If `--force-with-lease` is rejected (someone pushed to the branch after you fetched), stop immediately and output:

```
Force-push rejected. Another commit was pushed to <BRANCH> after you fetched.

1. Fetch the latest state: git fetch origin
2. Inspect the conflicting commits: git log origin/<BRANCH>
3. Re-run /pr-merge to restart from the rebase step.

Do NOT retry with bare --force.
```

Do NOT proceed further.

### Step 4 — verify unresolved review threads have replies

Fetch review threads and the current user's login. Inline review threads are scoped to a file/line; top-level PR review bodies are NOT review threads and are not part of this check.

**Path A — MCP:** Call the discovered `*list_pull_request_review_threads*` tool for `<PR_NUMBER>`, and the `*viewer*` / `*get_authenticated_user*` tool to get the current login. If the tool surfaces pagination cursors, follow them until all threads (and all comments within each thread) are fetched.

**Path B — gh CLI fallback:** Resolve `<OWNER>` and `<REPO>` from `git remote get-url origin`, then run the paginated query below. Repeat with `after: "<endCursor>"` (substituted into `reviewThreads(first: 100, after: ...)`) until `reviewThreads.pageInfo.hasNextPage` is `false`. For any thread where `comments.pageInfo.hasNextPage` is `true`, paginate that thread's comments separately by re-querying with the thread's node ID until exhausted.

```bash
gh api graphql \
  -F owner="<OWNER>" -F name="<REPO>" -F number=<PR_NUMBER> \
  -f query='
    query($owner: String!, $name: String!, $number: Int!) {
      viewer { login }
      repository(owner: $owner, name: $name) {
        pullRequest(number: $number) {
          reviewThreads(first: 100) {
            pageInfo { hasNextPage endCursor }
            nodes {
              id
              isResolved
              comments(first: 100) {
                pageInfo { hasNextPage endCursor }
                nodes {
                  author { login }
                  createdAt
                  path
                  line
                  originalLine
                }
              }
            }
          }
        }
      }
    }'
```

**Fail closed on fetch errors.** If the GraphQL call returns a non-zero exit code, the response contains an `errors` array, `data.repository.pullRequest` is `null`, or `viewer.login` is missing/empty, STOP IMMEDIATELY. Output:

```
Failed to fetch review threads or viewer identity.

Response:
<raw response>

Resolve the underlying issue (auth scope, network, or PR access), then re-run /pr-merge. Do NOT proceed to merge.
```

Do not call any tools after this output. Treating a failed fetch as an empty inspection set is forbidden.

From a successful response, build the inspection set: every thread where `isResolved == false`.

For each inspected thread, sort `comments.nodes` by `createdAt` ascending and classify it:
- **replied** — the thread has at least one viewer comment whose `createdAt` is strictly later than every non-viewer comment's `createdAt` (i.e., the viewer has the last word).
- **unreplied** — otherwise (no viewer comment at all, OR the most recent comment from a non-viewer is later than the viewer's latest comment, meaning a reviewer follow-up is unanswered).

If any thread is **unreplied**, STOP IMMEDIATELY. Output:

```
Unreplied review threads detected (<N>):

- <path>:<line or originalLine>  (reviewer: <root-comment author.login>)
- ...

Please respond to each thread before merging:
  1. Run /pr-review-apply to draft and submit replies.
  2. Re-run /pr-merge once every thread has your reply.

Do NOT proceed further.
```

Do not call any tools after this output.

If every inspected thread is classified **replied**, retain the list of their `id` values as `<THREADS_TO_RESOLVE>` for the next step.

### Step 5 — resolve replied review threads

If `<THREADS_TO_RESOLVE>` is empty (no unresolved threads remain), skip to Step 6.

Otherwise, for each `<THREAD_ID>` in `<THREADS_TO_RESOLVE>`:

**Path A — MCP:** Call the discovered `*resolve_review_thread*` tool with `threadId`: `<THREAD_ID>`.

**Path B — gh CLI fallback:**

```bash
gh api graphql -F threadId="<THREAD_ID>" \
  -f query='mutation($threadId: ID!) {
    resolveReviewThread(input: { threadId: $threadId }) {
      thread { isResolved }
    }
  }'
```

Confirm the response shows `thread.isResolved == true`. If any call fails or returns `isResolved == false`, STOP IMMEDIATELY. Output:

```
Failed to resolve thread <THREAD_ID>.

Response:
<raw response>

Resolve the thread manually via the GitHub UI, then re-run /pr-merge.
```

Do not proceed further.

After all threads resolve successfully, output one line and continue:

```
Resolved <N> review thread(s).
```

### Step 6 — verify Test Plan

Fetch the PR body:

**Path A — MCP:** Call `*get_pull_request*` and extract the `body` field.

**Path B — gh CLI fallback:**

```bash
gh pr view <PR_NUMBER> --json body -q .body
```

Parse the `## Test Plan` section:
- **Section absent**: Stop immediately and output:
  ```
  No Test Plan found. Add a `## Test Plan` section to the PR body, then re-run /pr-merge.

  Example:
  ## Test Plan
  - [ ] Run `npm test`
  - [ ] Verify the feature in the browser
  ```
  Do NOT proceed further.
- **Section present, all items already checked (`- [x]`)**: Skip to the merge step.
- **Section present, unchecked items (`- [ ]`) found**: Continue below.

#### Classify each unchecked item

For each item, apply these rules in order:

| Rule | Classification |
|---|---|
| Text contains any of: `browser`, `UI`, `visual`, `manually`, `staging`, `production`, `open the`, `click`, `navigate`, `screenshot`, `in the app`, `in the browser` | **Manual** — stop; do not evaluate further rules |
| Text contains an inline backtick command (e.g. `` `npm test` ``) | **Auto** |
| Anything else | **Manual** |

#### Auto-verifiable path

For each **Auto** item:

1. Extract the backtick command literally from the item text.
2. Run `<extracted command>` in the repository root.
3. **Exit code 0 (pass):** Mark the item done silently and continue to the next item.
4. **Non-zero exit code (fail):** Stop immediately. Output:
   ```
   Test Plan auto-verification failed

   Item     : <item text>
   Command  : <extracted command>
   Exit code: <exit code>

   Output (last 50 lines):
   <command stdout/stderr, capped at 50 lines>

   Fix the issue and re-run /pr-merge. Do NOT proceed to the merge.
   ```
   Do NOT continue to the next item or to Step 8.

#### Manual path

For each **Manual** item, present it to the user one at a time:

```
Test Plan verification (<n> items remaining)

[ ] <item text>
Completed? [yes / no]
```

| User input | Action |
|---|---|
| `yes` or `y` | Mark item done, proceed to next item |
| `no` or `n` | Stop immediately. Tell the user to complete the item and re-run `/pr-merge`. Do NOT proceed to the merge step. |

#### Update the PR body

Once all items are verified (auto or manual), update the PR body by replacing each verified `- [ ]` with `- [x]` **within the `## Test Plan` section only** (do not modify checkboxes in other sections):

**Path A — MCP:** Call `*update_pull_request*` with the updated body.

**Path B — gh CLI fallback:**

```bash
gh pr edit <PR_NUMBER> --body-file - <<'BODY'
<updated body>
BODY
```

### Step 7 — re-check for new unresolved threads

Step 6 can take arbitrary wall-clock time (manual prompts, long auto-test commands), during which reviewers may file new threads. Before merging, re-run the Step 4 fetch (same paginated GraphQL query, same fail-closed rules).

- If the new inspection set is **empty** (no `isResolved == false` threads), continue to Step 8.
- If any thread is **unreplied**, STOP IMMEDIATELY and emit the same "Unreplied review threads detected" output as Step 4. Do NOT merge.
- If every inspected thread is **replied**, resolve those new `<THREAD_ID>` values using the Step 5 procedure (one `resolveReviewThread` mutation per thread, fail closed on any non-`true` response), then continue to Step 8.

Do not skip this re-check even if Step 4 found zero unresolved threads — new threads may have been filed since.

### Step 8 — merge the PR

Always use the merge commit method. Never squash or rebase-fast-forward.

**Path A — MCP:** Call the discovered `*merge_pull_request*` tool with `pull_number` (or equivalent): `<PR_NUMBER>` and `merge_method`: `"merge"`.

**Path B — gh CLI fallback:**

```bash
gh pr merge <PR_NUMBER> --merge
```

### Step 9 — report result

Retrieve and output the merge commit SHA and the PR URL:

**Path A — MCP:** Extract the merge commit SHA from the `*merge_pull_request*` tool response (look for a commit SHA or `merge_commit_sha` field in the response).

**Path B — gh CLI fallback:**

```bash
gh pr view <PR_NUMBER> --json mergeCommit,url -q '"\(.mergeCommit.oid) \(.url)"'
```

If the SHA cannot be retrieved from either path, report the merge as successful but warn the user that the SHA is unavailable.

