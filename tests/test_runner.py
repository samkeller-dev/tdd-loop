"""Unit tests for tdd_loop.runner — no LLM, no network."""

from pathlib import Path

import pytest

from tdd_loop.runner import run

FIXTURE = Path(__file__).parent / "fixtures" / "test_add.py"


GOOD_CODE = "def add(a, b):\n    return a + b\n"
BAD_CODE = "def add(a, b):\n    return a - b\n"
SYNTAX_ERROR = "def add(a, b)\n    return a + b\n"
INFINITE_LOOP = "def add(a, b):\n    while True:\n        pass\n"


def test_runner_passes_with_correct_solution():
    result = run(GOOD_CODE, FIXTURE, timeout_s=15)
    assert result.passed == 3
    assert result.failed == 0
    assert result.total == 3
    assert result.first_traceback is None


def test_runner_reports_failures_and_traceback():
    result = run(BAD_CODE, FIXTURE, timeout_s=15)
    assert result.failed >= 1
    assert result.passed + result.failed == result.total
    assert result.total == 3
    assert result.first_traceback is not None
    assert "assert" in result.first_traceback.lower() or "AssertionError" in result.first_traceback


def test_runner_handles_syntax_error_in_solution():
    result = run(SYNTAX_ERROR, FIXTURE, timeout_s=15)
    # Collection error → failed should be > 0, passed should be 0.
    assert result.passed == 0
    assert result.failed >= 1


def test_runner_enforces_timeout():
    result = run(INFINITE_LOOP, FIXTURE, timeout_s=2)
    assert result.failed >= 1
    assert "TIMEOUT" in result.output_tail
    assert result.first_traceback and "timeout" in result.first_traceback.lower()


def test_runner_output_tail_is_bounded():
    huge_print = "def add(a, b):\n    print('x' * 10_000)\n    return a + b\n"
    result = run(huge_print, FIXTURE, timeout_s=15)
    # 2KB tail + small prefix.
    assert len(result.output_tail) < 4096
