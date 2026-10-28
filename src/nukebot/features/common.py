"""Common result and context types for feature modules."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class Result:
    action: str
    success: int = 0
    failed: int = 0
    skipped: int = 0
    errors: list[str] = field(default_factory=list)
    details: dict[str, Any] = field(default_factory=dict)

    def add_error(self, message: str) -> None:
        self.failed += 1
        self.errors.append(message)

    def merge(self, other: "Result") -> "Result":
        self.success += other.success
        self.failed += other.failed
        self.skipped += other.skipped
        self.errors.extend(other.errors)
        return self

    def summary(self) -> str:
        return f"{self.action}: success={self.success}, failed={self.failed}, skipped={self.skipped}"


@dataclass
class Context:
    client: Any
    guild: Any
    rate_limiter: Any
    dry_run: Any
    mode: str
    logger: Any
    config: Any = None
