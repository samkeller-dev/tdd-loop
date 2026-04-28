"""Prompt templates for the initial attempt and the failure-driven refine step."""

from __future__ import annotations

from .schemas import Attempt

_JSON_INSTRUCTION = """\
Respond with ONLY a single JSON object matching this schema:
{
  "reasoning": "<brief plan or post-mortem of the previous attempt>",
  "code": "<full text of solution.py — no markdown fences, no comments needed>"
}
The code must be a complete Python module the test file can import directly.
Do not include the test file in your response. Do not wrap the JSON in
markdown. Do not emit anything outside the JSON object.
"""


def build_initial_prompt(spec: str, test_file: str) -> str:
    return f"""\
You are a careful Python engineer. You will be given a problem spec and the
exact pytest test file that will judge your solution. Write a complete
`solution.py` that makes every test pass.

# Problem spec

{spec}

# Test file (pytest will run this against your solution.py)

```python
{test_file}
```

# Output format

{_JSON_INSTRUCTION}
"""


def build_refine_prompt(
    spec: str,
    test_file: str,
    attempts: list[Attempt],
) -> str:
    """Show the model its last attempt and the failure, ask for a corrected version."""
    last = attempts[-1]
    failed_names = _failed_test_names(last.result.output_tail)
    failed_summary = (
        ", ".join(failed_names) if failed_names else "(see traceback below)"
    )
    traceback = last.result.first_traceback or "(no traceback captured)"

    return f"""\
You are a careful Python engineer iterating on a failing solution. Your
previous attempt did not pass all the tests. Read the spec, the tests, your
last attempt, and the failure output, then produce a corrected `solution.py`.

# Problem spec

{spec}

# Test file

```python
{test_file}
```

# Your previous attempt (attempt {last.n})

```python
{last.code}
```

# What happened when pytest ran it

Passed: {last.result.passed} / {last.result.total}
Failed tests: {failed_summary}

First traceback:
```
{traceback}
```

Output tail:
```
{last.result.output_tail}
```

# Your task

In `reasoning`, briefly state *why* the previous attempt failed before writing
the new implementation. Then in `code` produce the full corrected
`solution.py`. Do not just patch — emit the entire file.

If the same line of logic has now failed more than once, change the *shape*
of the solution (e.g. an explicit if/elif/else ladder instead of a nested
ternary) — small edits to a buggy expression often reproduce the bug.

{_JSON_INSTRUCTION}
"""


def _failed_test_names(output_tail: str) -> list[str]:
    """Best-effort scrape of failing test ids from pytest's short summary."""
    names: list[str] = []
    for line in output_tail.splitlines():
        line = line.strip()
        if line.startswith("FAILED "):
            # e.g. "FAILED test_solution.py::test_basic - AssertionError: ..."
            after = line[len("FAILED ") :]
            names.append(after.split(" ", 1)[0])
    return names
