"""Sandboxed pytest runner.

Writes the candidate solution and the challenge's test file into a temporary
directory, runs pytest with --json-report under a hard timeout, and parses the
report into a TestResult. The tempdir is cleaned up on exit.

Sandboxing caveat: this is *isolation by convention*, not security. The
candidate code runs in the same OS user as the loop. For untrusted models,
wrap this in a container or firejail.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

from .schemas import TestResult

OUTPUT_TAIL_BYTES = 2048


def _tail(text: str, n_bytes: int = OUTPUT_TAIL_BYTES) -> str:
    if len(text) <= n_bytes:
        return text
    return "...[truncated]...\n" + text[-n_bytes:]


def _first_traceback(report: dict | None, stdout: str) -> str | None:
    """Pull the first failing test's traceback out of the json report.

    Falls back to scanning stdout for a `Traceback (most recent call last):`
    block when the report isn't available (e.g. on collection failure).
    """
    if report:
        for test in report.get("tests", []):
            if test.get("outcome") == "failed":
                call = test.get("call") or {}
                long = call.get("longrepr") or test.get("longrepr")
                if long:
                    return long if isinstance(long, str) else str(long)
        for collector in report.get("collectors", []):
            if collector.get("outcome") == "failed":
                long = collector.get("longrepr")
                if long:
                    return long if isinstance(long, str) else str(long)
    if "Traceback (most recent call last):" in stdout:
        idx = stdout.index("Traceback (most recent call last):")
        return stdout[idx : idx + 4000]
    return None


def run(
    candidate_code: str,
    test_file: Path,
    *,
    timeout_s: float = 30.0,
    solution_filename: str = "solution.py",
) -> TestResult:
    """Execute pytest on candidate_code against test_file in a tempdir."""
    test_file = Path(test_file)
    started = time.monotonic()

    with tempfile.TemporaryDirectory(prefix="tdd_loop_") as td:
        td_path = Path(td)
        (td_path / solution_filename).write_text(candidate_code, encoding="utf-8")
        shutil.copy(test_file, td_path / test_file.name)
        report_path = td_path / "report.json"

        cmd = [
            sys.executable,
            "-m",
            "pytest",
            test_file.name,
            "--json-report",
            f"--json-report-file={report_path.name}",
            "-q",
            "--tb=short",
            "-p",
            "no:cacheprovider",
        ]
        try:
            proc = subprocess.run(
                cmd,
                cwd=td_path,
                capture_output=True,
                text=True,
                timeout=timeout_s,
                check=False,
            )
            stdout = proc.stdout or ""
            stderr = proc.stderr or ""
        except subprocess.TimeoutExpired as exc:
            duration = time.monotonic() - started
            tail = _tail((exc.stdout or "") + (exc.stderr or ""))
            return TestResult(
                passed=0,
                failed=1,
                total=1,
                duration_s=duration,
                output_tail=f"[TIMEOUT after {timeout_s}s]\n{tail}",
                first_traceback=f"Test run exceeded {timeout_s}s timeout.",
            )

        duration = time.monotonic() - started
        report: dict | None = None
        if report_path.exists():
            try:
                report = json.loads(report_path.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                report = None

        if report:
            summary = report.get("summary", {}) or {}
            passed = int(summary.get("passed", 0))
            failed = int(summary.get("failed", 0)) + int(summary.get("error", 0))
            total = int(summary.get("total", passed + failed))
            # Collection failure: pytest writes a report but with no tests
            # collected. Surface that as a failure rather than "0/0 passed".
            collector_errors = sum(
                1 for c in report.get("collectors", [])
                if c.get("outcome") == "failed"
            )
            if collector_errors and total == 0:
                failed = collector_errors
                total = collector_errors
        else:
            # pytest crashed before writing the report.
            passed = 0
            failed = 1
            total = 1

        return TestResult(
            passed=passed,
            failed=failed,
            total=total,
            duration_s=duration,
            output_tail=_tail(stdout + ("\n--- stderr ---\n" + stderr if stderr else "")),
            first_traceback=_first_traceback(report, stdout + "\n" + stderr),
        )
