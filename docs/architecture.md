# Architecture

## The loop

`tdd-loop` is a single-agent, single-tool **agentic loop**: a model
generates code, a deterministic test runner judges it, the failure becomes
the next prompt. There is no branching, no tree search, no scoring —
just spec → generate → test → diff-of-failure → generate, repeated until
either every test passes or `max_attempts` is exhausted.

```
                 ┌───────────────────┐
                 │  challenge dir/   │
                 │   spec.md         │
                 │   test_solution.py│
                 └────────┬──────────┘
                          │
                          ▼
              ┌─────────────────────────┐
              │  build_initial_prompt   │   prompts.py
              └────────────┬────────────┘
                           │
                           ▼
              ┌─────────────────────────┐
              │   Ollama HTTP /api/gen  │   llm.py
              │   model=mistral:7b      │   format=json
              │   {reasoning, code}     │
              └────────────┬────────────┘
                           │
                           ▼
              ┌─────────────────────────┐
              │  sandbox runner         │   runner.py
              │  tempdir + subprocess   │
              │  pytest --json-report   │
              │  30s timeout            │
              └────────────┬────────────┘
                           │
                  ┌────────┴─────────┐
                  ▼                  ▼
               passed?            failed?
                  │                  │
                  ▼                  ▼
              ┌──────┐    ┌────────────────────────┐
              │ DONE │    │ build_refine_prompt    │
              └──────┘    │ (spec + tests + last   │
                          │  code + traceback +    │
                          │  failed test names)    │
                          └────────────┬───────────┘
                                       │
                                       └── back to Ollama
```

Each attempt produces an `Attempt` record (Pydantic model) containing the
model's `reasoning`, the candidate `code`, and the `TestResult`. The full
`LoopState` (challenge id, model, all attempts, final status, timestamps)
is serialised to `summary.json` at the end of the run.

## Module boundaries

| Module                  | Responsibility                                              | External I/O     |
|-------------------------|-------------------------------------------------------------|------------------|
| `tdd_loop/schemas.py`   | Pydantic v2 models — `TestResult`, `Attempt`, `LoopState`. | none             |
| `tdd_loop/llm.py`       | Ollama HTTP client. `format=json` constrained output.      | localhost:11434  |
| `tdd_loop/prompts.py`   | `build_initial_prompt`, `build_refine_prompt`. Pure.       | none             |
| `tdd_loop/runner.py`    | Subprocess pytest runner with timeout + tempdir.           | filesystem, child process |
| `tdd_loop/loop.py`      | Wires everything; injection points for tests.              | composed         |
| `tdd_loop/cli.py`       | Click commands `run` / `benchmark`; Rich transcript.       | stdout, stderr   |

The loop accepts `llm` and `runner` as injectable parameters. Unit tests
in `tests/test_loop.py` substitute a `FakeLLM` returning canned responses
and a fake runner returning canned `TestResult`s, so the loop's
control-flow logic can be exercised without touching Ollama or pytest.

## Constrained output

We rely on Ollama's `format="json"` mode plus an in-prompt schema
description for the model output to be reliably parseable. The contract
is two fields:

```json
{ "reasoning": "...", "code": "..." }
```

If the model emits malformed JSON despite the constraint, the loop
records an `error` final-status with the exception message rather than
crashing — this surfaces in the run artefacts.

## Sandboxing

The runner uses `tempfile.TemporaryDirectory` + `subprocess.run(timeout=…)`.
This is **not** a security boundary: candidate code runs as the same OS
user as the loop. It's sufficient for trusted local model output (the
threat model here is "the model writes a buggy infinite loop", not "the
model is adversarial"). For untrusted use, wrap each invocation in a
container, firejail, or seccomp profile.

## Why pytest-json-report

Parsing pytest's human-readable stdout is fragile. `pytest-json-report`
gives a structured `report.json` with per-test outcomes, durations, and
longreprs (tracebacks). The runner reads that file directly, falling
back to a stdout scrape only when the report isn't written (e.g. on a
collection error).
