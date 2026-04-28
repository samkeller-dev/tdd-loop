"""Click CLI: `tdd-loop run` and `tdd-loop benchmark`."""

from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path

import click
from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax
from rich.table import Table

from . import loop as loop_mod
from .llm import DEFAULT_MODEL, OllamaClient
from .schemas import Attempt

console = Console()


def _make_attempt_callback() -> "callable[[Attempt], None]":
    def cb(attempt: Attempt) -> None:
        r = attempt.result
        status = "[green]PASS[/green]" if r.failed == 0 and r.total > 0 else "[red]FAIL[/red]"
        header = (
            f"Attempt {attempt.n} — {status} "
            f"({r.passed}/{r.total} in {r.duration_s:.1f}s)"
        )
        console.print(Panel(attempt.reasoning.strip() or "(no reasoning)", title=f"{header} — reasoning"))
        if attempt.code.strip():
            console.print(Panel(
                Syntax(attempt.code, "python", line_numbers=False, word_wrap=True),
                title=f"Attempt {attempt.n} — code",
            ))
        if r.failed and r.first_traceback:
            console.print(Panel(r.first_traceback, title=f"Attempt {attempt.n} — first traceback", border_style="red"))

    return cb


@click.group()
@click.version_option()
def cli() -> None:
    """Self-correcting LLM coding loop."""


@cli.command("run")
@click.argument("challenge_dir", type=click.Path(exists=True, file_okay=False, path_type=Path))
@click.option("--max-attempts", type=int, default=5, show_default=True)
@click.option("--model", default=DEFAULT_MODEL, show_default=True)
@click.option("--host", default="http://localhost:11434", show_default=True)
@click.option("--timeout", "test_timeout_s", type=float, default=30.0, show_default=True,
              help="Per-attempt subprocess test timeout in seconds.")
@click.option("--out-dir", type=click.Path(path_type=Path), default=None,
              help="Directory to write attempt_NN.{py,json} and summary.json. "
                   "Defaults to runs/{timestamp}-{challenge}.")
def run_cmd(
    challenge_dir: Path,
    max_attempts: int,
    model: str,
    host: str,
    test_timeout_s: float,
    out_dir: Path | None,
) -> None:
    """Run the loop on a single challenge."""
    console.rule(f"[bold]tdd-loop[/bold]  challenge=[cyan]{challenge_dir.name}[/cyan]  model=[cyan]{model}[/cyan]")
    llm = OllamaClient(model=model, host=host)
    state = loop_mod.run_loop(
        challenge_dir,
        max_attempts=max_attempts,
        model=model,
        llm=llm,
        test_timeout_s=test_timeout_s,
        on_attempt=_make_attempt_callback(),
    )

    if out_dir is None:
        ts = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
        out_dir = Path("runs") / f"{ts}-{challenge_dir.name}"
    loop_mod.write_run_artefacts(state, out_dir)

    final_color = {"solved": "green", "exhausted": "yellow", "error": "red"}[state.final_status]
    console.rule(
        f"[bold {final_color}]{state.final_status.upper()}[/]  "
        f"attempts={len(state.attempts)}/{state.max_attempts}  "
        f"artefacts=[dim]{out_dir}[/dim]"
    )
    if state.final_status != "solved":
        sys.exit(1)


@cli.command("benchmark")
@click.argument("challenge_dirs", nargs=-1, type=click.Path(exists=True, file_okay=False, path_type=Path))
@click.option("--all", "all_challenges", is_flag=True, help="Run every challenges/* dir.")
@click.option("--max-attempts", type=int, default=5, show_default=True)
@click.option("--model", default=DEFAULT_MODEL, show_default=True)
@click.option("--host", default="http://localhost:11434", show_default=True)
@click.option("--timeout", "test_timeout_s", type=float, default=30.0, show_default=True)
@click.option("--runs-dir", type=click.Path(path_type=Path), default=None,
              help="If set, also write per-challenge attempt artefacts under this directory.")
def benchmark_cmd(
    challenge_dirs: tuple[Path, ...],
    all_challenges: bool,
    max_attempts: int,
    model: str,
    host: str,
    test_timeout_s: float,
    runs_dir: Path | None,
) -> None:
    """Run every challenge (or the listed ones) and print a markdown results table."""
    if all_challenges:
        root = Path("challenges")
        if not root.is_dir():
            raise click.UsageError("--all expects a 'challenges/' directory in the cwd.")
        challenge_dirs = tuple(sorted(p for p in root.iterdir() if p.is_dir()))
    if not challenge_dirs:
        raise click.UsageError("No challenges given. Pass paths or --all.")

    llm = OllamaClient(model=model, host=host)

    # Live progress: print compact one-liner per attempt to stderr.
    def cb(attempt: Attempt) -> None:
        r = attempt.result
        status = "PASS" if r.failed == 0 and r.total > 0 else "FAIL"
        console.print(
            f"  [dim]attempt {attempt.n}: {status} "
            f"{r.passed}/{r.total} ({r.duration_s:.1f}s)[/dim]"
        )

    states = []
    table = Table(title=f"benchmark — {model}")
    table.add_column("Challenge")
    table.add_column("Status")
    table.add_column("Attempts")
    table.add_column("Time (s)")
    for cd in challenge_dirs:
        console.rule(f"[cyan]{cd.name}[/cyan]")
        state = loop_mod.run_loop(
            cd,
            max_attempts=max_attempts,
            model=model,
            llm=llm,
            test_timeout_s=test_timeout_s,
            on_attempt=cb,
        )
        states.append(state)
        if runs_dir is not None:
            loop_mod.write_run_artefacts(state, runs_dir / cd.name)
        elapsed = (
            (state.ended_at - state.started_at).total_seconds()
            if state.ended_at
            else 0.0
        )
        color = {"solved": "green", "exhausted": "yellow", "error": "red"}[state.final_status]
        table.add_row(
            cd.name,
            f"[{color}]{state.final_status}[/{color}]",
            f"{len(state.attempts)}/{state.max_attempts}",
            f"{elapsed:.1f}",
        )

    console.print(table)
    console.rule("markdown")
    # Plain-print the markdown so it can be redirected/copy-pasted into the README.
    click.echo(loop_mod.benchmark_table(states))


if __name__ == "__main__":
    cli()
