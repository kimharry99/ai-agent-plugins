# Review Context: Test Coverage

**Purpose.** Verify that the diff's behavioral changes are accompanied by adequate tests — not raw coverage percentages, but coverage of the *right scenarios*: new public behavior is tested, bug fixes have regression tests, and test code in the diff is sound.

## Scope

This context activates whenever a diff adds or modifies non-trivial behavior (new functions, changed logic, bug fixes). It uniquely evaluates **absence**: a missing test is a finding. Anchor a missing-test finding to the `file:line` of the untested new/changed behavior — not to a non-existent test line. The reviewer may read outside the diff (existing test files, sibling test modules) to confirm whether coverage already exists, but the finding's anchor stays inside the diff.

**Every checkpoint evaluates only behavior added or modified within the diff hunks.** This context never instructs the reviewer to flag a missing test for pre-existing untested code outside the diff — this keeps the review within the reviewer agent's "stay inside the diff" rule.

Pure non-behavioral diffs (formatting, comment-only edits, renames with no logic change, documentation edits) yield no findings; this context stays silent. Test-quality checkpoints (4–6) apply to test code **added or modified in the diff**. Implementation correctness defers to the `architect` context — `test-coverage` only asks whether behavior is *tested*, not whether it is *correct*.

## Checkpoints

### 1. New behavior is tested

Every new **public** function, method, endpoint, or exported symbol introduced in the diff must have at least one test that exercises it. Private helpers covered transitively by a tested public entry point are fine — do not require a direct test for each private helper.

Anchor the finding to the line of the new public symbol, not to a missing test file.

```python
# BAD: new public function with no test anywhere (Critical)
def calculate_discount(price: float, rate: float) -> float:
    return price * (1 - rate)

# GOOD: an accompanying test exists
def test_calculate_discount_applies_rate():
    assert calculate_discount(100.0, 0.1) == 90.0
```

### 2. Bug-fix regression test

If the diff fixes a bug, there must be a test that would **fail without the fix** — a test whose existence prevents the bug from regressing. Anchor the finding to the fixed line.

```python
# BAD: bug fixed but no regression test (Critical)
# was: return items[0] — raised IndexError on empty list
def first_or_none(items):
    return items[0] if items else None

# GOOD: regression test added
def test_first_or_none_returns_none_for_empty_list():
    assert first_or_none([]) is None
```

### 3. Edge & error paths

Boundary inputs (null/empty/zero/maximum) and error/exception branches **introduced in the diff** are exercised by at least one test each.

### 4. Specific, meaningful assertions

Tests in the diff assert the **actual expected value**, not just non-nullness or truthiness. Each test covers one logical behavior.

```python
# BAD: vacuous assertion (Important)
def test_parse_result():
    result = parse("2024-01-15")
    assert result is not None

# GOOD: asserts the specific value
def test_parse_returns_correct_date():
    assert parse("2024-01-15") == date(2024, 1, 15)
```

### 5. Test isolation

Tests added or modified in the diff do not depend on execution order and do not share mutable state between tests. Each test sets up its own fixtures or test data.

### 6. Test quality

Tests in the diff assert observable output and public contract, not private internals or incidental call counts (unless the interaction *is* the contract). Test names describe the scenario and expected outcome (e.g. `test_returns_empty_list_when_input_is_none`). Near-duplicate test cases are parameterized rather than copy-pasted.

## Priority hints

- **Critical** — A new public function/method/endpoint/exported symbol has no test; a bug fix has no regression test. Both block approval.
- **Important** — Missing edge/error-path coverage for behavior the diff introduces; weak or vacuous assertions (asserting truthiness instead of the specific expected value); tests with shared mutable state or execution-order dependence.
- **Suggestion** — Tests assert implementation details (private methods, call counts) rather than observable behavior; vague test names; un-parameterized near-duplicate test cases.
