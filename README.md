# tdd-loop

A self-correcting **agentic loop** for code generation. Given a problem
spec and a `pytest` test file, it asks **Mistral 7B Instruct** (running
locally via **Ollama**) for a `solution.py`, runs the tests in a
**sandboxed subprocess** with a 30s timeout, parses the structured
`pytest-json-report` output, feeds any failure back into the next prompt,
and iterates until the tests pass or `max_attempts` is exhausted.

The interesting bit is the loop, not the model: the same architecture —
**expected results → analyse actual results → next iteration** — drops in
unchanged for any problem that has a deterministic verifier.

## Frameworks

- **Ollama** (local) + **Mistral 7B Instruct**
- **`format=json`** constrained output for the model's `{reasoning, code}`
- **agentic loop / self-correction** — single agent, single tool, judged by tests
- **pytest** + **pytest-json-report** for machine-readable test outcomes
- **Pydantic v2** for loop-state schemas (`TestResult`, `Attempt`, `LoopState`)
- **sandboxed subprocess** execution (tempdir + 30s timeout)
- **Click** CLI + **Rich** transcript

## Architecture

```
spec.md  +  test_solution.py
            │
            ▼
   build_initial_prompt ──►  Ollama /api/generate (mistral:7b-instruct, format=json)
                                    │
                                    ▼  {reasoning, code}
                            sandbox runner: pytest --json-report  (30s timeout)
                                    │
                          pass?  ◄──┴──►  fail?
                            │             │
                          DONE     build_refine_prompt
                                   (spec + tests + last code +
                                    traceback + failed test names)
                                          │
                                          └──► Ollama /api/generate
```

See [`docs/architecture.md`](docs/architecture.md) for the full breakdown.

## Quickstart

Requires Python 3.11+, `pip`, and a running Ollama server with
`mistral:7b-instruct` pulled. The fastest way on a fresh machine:

```bash
# 1. Ollama (Docker — least invasive). On a host with no GPU support
#    configured, this runs on CPU; expect ~1–2 minutes per attempt.
docker run -d --name ollama -p 11434:11434 -v ollama:/root/.ollama ollama/ollama
docker exec ollama ollama pull mistral:7b-instruct

# 2. Install the loop
git clone https://github.com/samkeller-dev/tdd-loop && cd tdd-loop
pip install -e .

# 3. Run the unit tests (no Ollama needed; LLM is mocked)
pytest

# 4. Run the loop on a challenge
tdd-loop run challenges/01_fizzbuzz --max-attempts 5

# 5. Or benchmark every challenge
tdd-loop benchmark --all
```

`tdd-loop run` prints a Rich-formatted transcript of every attempt
(reasoning, code, traceback) and writes per-attempt artefacts under
`runs/<timestamp>-<challenge>/` (`attempt_NN.py`, `attempt_NN.json`,
`summary.json`).

## Example: a real correction

The committed sample at [`runs/sample-lru-cache/`](runs/sample-lru-cache/)
preserves every artefact from one real local run. Mistral 7B Instruct
needed three tries to pass the LRU-cache tests; the **loop watched it
fail twice and corrected itself each time**.

<!-- BEGIN: example-transcript -->

**Attempt 1** — collection error (0/1).

Reasoning the model gave: *"I will implement an LRU Cache using a
dictionary for storing key-value pairs and a doubly linked list to keep
track of the order of usage."*

The generated code had a typo — `nclass LRUCache:` instead of
`class LRUCache:` — so pytest couldn't even import the module:

```
test_solution.py:8: in test_basic_put_get
    ...
SyntaxError: invalid syntax
```

The loop fed that traceback back into the next prompt.

**Attempt 2** — 0/8.

Reasoning the model gave on attempt 2: *"In the previous attempt, the
class name was incorrectly defined as 'nclass LRUCache', which is invalid
syntax in Python. The correct syntax should be 'class LRUCache'."* It
fixed the syntax error correctly — but only emitted method stubs:

```python
class LRUCache:
    def __init__(self, capacity: int): ...
    def get(self, key) -> int: ...     # returns -1 if key is absent
    def put(self, key, value) -> None: ...
```

So now every test failed on `c.get(1)` returning `None`. That diagnosis
also became the next prompt.

**Attempt 3** — 8/8 ✅

Reasoning the model gave on attempt 3: *"In the previous attempt, the
`get` method was not implemented correctly, it always returned None
instead of the correct value or -1 when the key is missing."*

```python
class LRUCache:
    def __init__(self, capacity: int):
        self.cache = {}
        self.order = []
        self.capacity = capacity

    def get(self, key) -> int:
        if key in self.cache:
            self.order.remove(key)
            self.order.append(key)
            return self.cache[key]
        return -1

    def put(self, key, value) -> None:
        if key in self.cache:
            self.order.remove(key)
            self.order.append(key)
            self.cache[key] = value
        else:
            self.cache[key] = value
            self.order.append(key)
            if len(self.cache) > self.capacity:
                lru = self.order.pop(0)
                del self.cache[lru]
```

All 8 tests pass — including the eviction-order and capacity-1 cases.
The model never saw a hint about *what* was wrong; it inferred the bug
each time from the failing test name and traceback that the loop fed
back into the prompt. That's the whole game: the **agentic loop** is
the corrective signal, not the model.

<!-- END: example-transcript -->

## Benchmark

5 challenges, each with a `spec.md` and a parametrised `pytest` file.
Every run is `mistral:7b-instruct` via local Ollama, `--max-attempts 4`,
temperature 0.6, on CPU.

<!-- BEGIN: benchmark-table -->

| Challenge | Status | Attempts used | First-pass? | Total time (s) |
|---|---|---|---|---|
| `01_fizzbuzz` | solved | 1/4 | yes | 154.7 |
| `02_balanced_parens` | exhausted | 4/4 | no | 733.1 |
| `03_roman_numerals` | exhausted | 4/4 | no | 795.3 |
| `04_lru_cache` | solved | 3/4 | no | 523.5 |
| `05_word_frequency` | error | 3/4 | no | 329.4 |

**2/5 solved** on a single CPU run. Calibration on what this means:

- `01_fizzbuzz` solved on attempt 1.
- `04_lru_cache` solved on attempt 3 — the loop's corrective effect
  driving the win (see [transcript above](#example-a-real-correction)).
- `02_balanced_parens` and `03_roman_numerals` exhausted at 4 attempts:
  Mistral 7B kept producing structurally-similar wrong code and the
  refine prompt couldn't dislodge it. Bigger or coder-tuned models do
  much better here; the limiting factor is the model, not the loop.
- `05_word_frequency` errored on a 6-minute generation timeout (the
  longest CPU-only Mistral 7B took on this hardware). Larger
  `--timeout` would convert this into another exhausted-or-solved.

Re-runs vary because temperature is 0.6.

<!-- END: benchmark-table -->

To reproduce: `tdd-loop benchmark --all --runs-dir runs/benchmark`.


## Repo layout

```
tdd_loop/         core library — schemas, llm, runner, prompts, loop, cli
challenges/       five problem specs + tests
tests/            unit tests for the runner and the loop (mocked LLM)
runs/             persisted run artefacts (sample-fizzbuzz/ committed)
docs/             architecture writeup
```
