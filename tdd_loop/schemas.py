"""Pydantic v2 schemas for loop state and LLM I/O."""

from __future__ import annotations

from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field


class TestResult(BaseModel):
    """Outcome of running a candidate solution against the challenge tests."""

    passed: int = 0
    failed: int = 0
    total: int = 0
    duration_s: float = 0.0
    output_tail: str = ""
    first_traceback: Optional[str] = None


class AttemptOutput(BaseModel):
    """Constrained JSON shape we ask Ollama to emit each turn."""

    reasoning: str = Field(
        ...,
        description="Brief plan or, after a failure, why the previous attempt was wrong.",
    )
    code: str = Field(
        ...,
        description="Complete contents of solution.py.",
    )


class Attempt(BaseModel):
    n: int
    timestamp: datetime
    reasoning: str
    code: str
    result: TestResult


class LoopState(BaseModel):
    challenge: str
    model: str
    max_attempts: int
    attempts: list[Attempt] = Field(default_factory=list)
    final_status: Literal["solved", "exhausted", "error"] = "exhausted"
    started_at: datetime
    ended_at: Optional[datetime] = None
