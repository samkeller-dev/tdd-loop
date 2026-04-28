"""The self-correcting iteration loop.

Wires together the Ollama client, the prompt builders, and the sandboxed
runner. Designed to be testable: the LLM client and the runner are injected,
so unit tests can supply a deterministic fake LLM and never touch a network.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Iterable, Optional

from . import prompts
from .llm import DEFAULT_MODEL, LLMClient, OllamaClient
from .runner import run as run_tests
from .schemas import Attempt, LoopState, TestResult

RunnerFn = Callable[[str, Path], TestResult]


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _default_runner(timeout_s: float) -> RunnerFn:
    def _run(code: str, test_file: Path) -> TestResult:
        return run_tests(code, test_file, timeout_s=timeout_s)

    return _run


def run_loop(
    challenge_dir: Path | str,
    *,
    max_attempts: int = 5,
    model: str = DEFAULT_MODEL,
    llm: Optional[LLMClient] = None,
    runner: Optional[RunnerFn] = None,
    test_timeout_s: float = 30.0,
    on_attempt: Callable[[Attempt], None] | None = None,
) -> LoopState:
    """Run the spec → generate → test → refine cycle until solved or exhausted.

    Args:
        challenge_dir: directory containing spec.md and test_solution.py.
        max_attempts: hard cap on iterations.
        model: Ollama model name (only used when ``llm`` is None).
        llm: optional injected LLM client (for tests).
        runner: optional injected runner fn(code, test_path) -> TestResult.
        test_timeout_s: per-attempt subprocess timeout.
        on_attempt: optional callback fired after each attempt completes —
            used by the CLI to emit a live transcript.
    """
    challenge_dir = Path(challenge_dir)
    spec = (challenge_dir / "spec.md").read_text(encoding="utf-8")
    test_path = challenge_dir / "test_solution.py"
    test_text = test_path.read_text(encoding="utf-8")

    llm_client = llm if llm is not None else OllamaClient(model=model)
    runner_fn = runner if runner is not None else _default_runner(test_timeout_s)

    state = LoopState(
        challenge=str(challenge_dir),
        model=model,
        max_attempts=max_attempts,
        attempts=[],
        final_status="exhausted",
        started_at=_utcnow(),
    )

    prompt = prompts.build_initial_prompt(spec, test_text)

    for n in range(1, max_attempts + 1):
        try:
            output = llm_client.generate(prompt)
        except Exception as exc:  # network failure, malformed JSON, etc.
            state.final_status = "error"
            state.attempts.append(
                Attempt(
                    n=n,
                    timestamp=_utcnow(),
                    reasoning=f"[llm error] {exc}",
                    code="",
                    result=TestResult(
                        passed=0,
                        failed=1,
                        total=1,
                        duration_s=0.0,
                        output_tail=str(exc),
                        first_traceback=str(exc),
                    ),
                )
            )
            state.ended_at = _utcnow()
            return state

        result = runner_fn(output.code, test_path)
        attempt = Attempt(
            n=n,
            timestamp=_utcnow(),
            reasoning=output.reasoning,
            code=output.code,
            result=result,
        )
        state.attempts.append(attempt)
        if on_attempt is not None:
            on_attempt(attempt)

        if result.failed == 0 and result.total > 0:
            state.final_status = "solved"
            state.ended_at = _utcnow()
            return state

        prompt = prompts.build_refine_prompt(spec, test_text, state.attempts)

    state.final_status = "exhausted"
    state.ended_at = _utcnow()
    return state


def write_run_artefacts(state: LoopState, out_dir: Path | str) -> Path:
    """Persist a run as attempt_NN.py / attempt_NN.json + summary.json."""
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    for attempt in state.attempts:
        stem = f"attempt_{attempt.n:02d}"
        (out / f"{stem}.py").write_text(attempt.code, encoding="utf-8")
        (out / f"{stem}.json").write_text(
            attempt.result.model_dump_json(indent=2), encoding="utf-8"
        )
    (out / "summary.json").write_text(
        state.model_dump_json(indent=2), encoding="utf-8"
    )
    return out


def benchmark(
    challenge_dirs: Iterable[Path | str],
    *,
    max_attempts: int = 5,
    model: str = DEFAULT_MODEL,
    llm: Optional[LLMClient] = None,
    test_timeout_s: float = 30.0,
    on_attempt: Callable[[Attempt], None] | None = None,
) -> list[LoopState]:
    """Run the loop against every challenge_dir and return the LoopStates."""
    results: list[LoopState] = []
    for cd in challenge_dirs:
        state = run_loop(
            cd,
            max_attempts=max_attempts,
            model=model,
            llm=llm,
            test_timeout_s=test_timeout_s,
            on_attempt=on_attempt,
        )
        results.append(state)
    return results


def benchmark_table(states: list[LoopState]) -> str:
    """Format benchmark results as a markdown table."""
    lines = [
        "| Challenge | Status | Attempts used | First-pass? | Total time (s) |",
        "|---|---|---|---|---|",
    ]
    for s in states:
        name = Path(s.challenge).name
        attempts = len(s.attempts)
        first_pass = "yes" if attempts == 1 and s.final_status == "solved" else "no"
        if s.ended_at and s.started_at:
            elapsed = (s.ended_at - s.started_at).total_seconds()
            elapsed_str = f"{elapsed:.1f}"
        else:
            elapsed_str = "-"
        lines.append(
            f"| `{name}` | {s.final_status} | {attempts}/{s.max_attempts} | "
            f"{first_pass} | {elapsed_str} |"
        )
    return "\n".join(lines)


def loopstate_to_json(state: LoopState) -> str:
    return json.dumps(json.loads(state.model_dump_json()), indent=2)
