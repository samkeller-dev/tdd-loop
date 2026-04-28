"""Unit tests for tdd_loop.loop — fully mocked LLM, no Ollama needed."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import pytest

from tdd_loop import loop as loop_mod
from tdd_loop import prompts as prompts_mod
from tdd_loop.schemas import AttemptOutput, TestResult


@pytest.fixture
def challenge(tmp_path: Path) -> Path:
    """Minimal fake challenge dir."""
    (tmp_path / "spec.md").write_text("Toy spec: implement add(a,b).")
    (tmp_path / "test_solution.py").write_text(
        "from solution import add\n\ndef test_a(): assert add(1,2)==3\n"
    )
    return tmp_path


@dataclass
class FakeLLM:
    """Returns a fixed sequence of canned responses, one per call."""
    responses: list[AttemptOutput]
    calls: list[str] = field(default_factory=list)

    def generate(self, prompt: str) -> AttemptOutput:
        self.calls.append(prompt)
        if not self.responses:
            raise RuntimeError("FakeLLM ran out of canned responses")
        return self.responses.pop(0)


def make_runner(results: list[TestResult]):
    """Returns a runner fn that yields the supplied TestResults in order."""
    seq = list(results)
    seen: list[tuple[str, Path]] = []

    def runner(code: str, test_path: Path) -> TestResult:
        seen.append((code, test_path))
        if not seq:
            raise RuntimeError("runner ran out of results")
        return seq.pop(0)

    runner.seen = seen  # type: ignore[attr-defined]
    return runner


def passing(total: int = 3) -> TestResult:
    return TestResult(passed=total, failed=0, total=total, duration_s=0.1, output_tail="ok")


def failing() -> TestResult:
    return TestResult(
        passed=0,
        failed=1,
        total=1,
        duration_s=0.1,
        output_tail="FAILED test_solution.py::test_a - AssertionError",
        first_traceback="AssertionError: 1 != 3",
    )


def test_loop_halts_on_first_success(challenge: Path):
    llm = FakeLLM([AttemptOutput(reasoning="r1", code="def add(a,b): return a+b")])
    runner = make_runner([passing()])
    state = loop_mod.run_loop(challenge, max_attempts=5, llm=llm, runner=runner)
    assert state.final_status == "solved"
    assert len(state.attempts) == 1
    assert len(llm.calls) == 1


def test_loop_retries_after_failure_then_solves(challenge: Path):
    llm = FakeLLM([
        AttemptOutput(reasoning="first try", code="def add(a,b): return a-b"),
        AttemptOutput(reasoning="ah, sign error", code="def add(a,b): return a+b"),
    ])
    runner = make_runner([failing(), passing()])
    state = loop_mod.run_loop(challenge, max_attempts=5, llm=llm, runner=runner)
    assert state.final_status == "solved"
    assert len(state.attempts) == 2
    # Second prompt must contain refine markers (the previous attempt's code
    # and the failure traceback).
    second_prompt = llm.calls[1]
    assert "previous attempt" in second_prompt.lower()
    assert "AssertionError" in second_prompt
    assert "def add(a,b): return a-b" in second_prompt


def test_loop_exhausts_max_attempts(challenge: Path):
    llm = FakeLLM([
        AttemptOutput(reasoning=f"try {i}", code=f"# try {i}") for i in range(3)
    ])
    runner = make_runner([failing(), failing(), failing()])
    state = loop_mod.run_loop(challenge, max_attempts=3, llm=llm, runner=runner)
    assert state.final_status == "exhausted"
    assert len(state.attempts) == 3
    assert len(llm.calls) == 3


def test_loop_records_llm_error(challenge: Path):
    class ExplodingLLM:
        def generate(self, prompt):
            raise RuntimeError("boom")

    runner = make_runner([])
    state = loop_mod.run_loop(challenge, max_attempts=3, llm=ExplodingLLM(), runner=runner)
    assert state.final_status == "error"
    assert len(state.attempts) == 1
    assert "boom" in state.attempts[0].reasoning


def test_loop_writes_artefacts(tmp_path: Path, challenge: Path):
    llm = FakeLLM([AttemptOutput(reasoning="r", code="def add(a,b): return a+b")])
    runner = make_runner([passing()])
    state = loop_mod.run_loop(challenge, max_attempts=2, llm=llm, runner=runner)
    out = tmp_path / "out"
    loop_mod.write_run_artefacts(state, out)
    assert (out / "summary.json").is_file()
    assert (out / "attempt_01.py").is_file()
    assert (out / "attempt_01.json").is_file()


def test_initial_prompt_contains_spec_and_tests():
    p = prompts_mod.build_initial_prompt("THE SPEC", "THE TESTS")
    assert "THE SPEC" in p
    assert "THE TESTS" in p
    assert "JSON" in p


def test_refine_prompt_extracts_failed_test_names():
    names = prompts_mod._failed_test_names(
        "FAILED test_solution.py::test_a - AssertionError\n"
        "FAILED test_solution.py::test_b - foo\n"
        "passed 0 failed 2"
    )
    assert names == ["test_solution.py::test_a", "test_solution.py::test_b"]


def test_strip_markdown_fence_removes_python_fence():
    from tdd_loop.llm import _strip_markdown_fence

    fenced = "```python\ndef add(a, b):\n    return a + b\n```\n"
    assert _strip_markdown_fence(fenced).strip() == "def add(a, b):\n    return a + b"


def test_strip_markdown_fence_passthrough_when_no_fence():
    from tdd_loop.llm import _strip_markdown_fence

    raw = "def add(a, b):\n    return a + b\n"
    assert _strip_markdown_fence(raw) == raw


def test_benchmark_table_format():
    from tdd_loop.schemas import LoopState, Attempt
    from datetime import datetime, timezone

    s = LoopState(
        challenge="challenges/01_fizzbuzz",
        model="mistral:7b-instruct",
        max_attempts=5,
        attempts=[Attempt(n=1, timestamp=datetime.now(timezone.utc),
                          reasoning="r", code="c", result=passing())],
        final_status="solved",
        started_at=datetime.now(timezone.utc),
        ended_at=datetime.now(timezone.utc),
    )
    md = loop_mod.benchmark_table([s])
    assert "| Challenge |" in md
    assert "01_fizzbuzz" in md
    assert "solved" in md
