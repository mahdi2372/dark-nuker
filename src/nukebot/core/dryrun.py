"""Dry-run context and helpers."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class DryRunContext:
    enabled: bool = False
    planned: list[dict] = field(default_factory=list)

    def record(self, action: str, target: str, count: int = 1) -> None:
        self.planned.append({"action": action, "target": target, "count": count})

    def is_dry(self) -> bool:
        return self.enabled

    def summary(self) -> str:
        if not self.planned:
            return "No planned actions."
        lines = [f"{item['action']}: {item['count']} x {item['target']}" for item in self.planned]
        return "\n".join(lines)
