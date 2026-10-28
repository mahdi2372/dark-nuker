"""Configuration loading and validation."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class Config:
    mode: str = "bot"
    max_concurrency: int = 5
    default_dry_run: bool = False
    backup_dir: str = "backups"
    log_level: str = "INFO"
    proxy: str | None = None
    abort_on_error: bool = False
    bulk_delete_batch_size: int = 100
    selfbot_max_concurrency: int = 3
    extra: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def load(cls, path: str | Path = "config.json") -> "Config":
        p = Path(path)
        if not p.exists():
            return cls()
        data = json.loads(p.read_text(encoding="utf-8"))
        known = {f.name for f in cls.__dataclass_fields__.values() if f.name != "extra"}
        values: dict[str, Any] = {}
        extra: dict[str, Any] = {}
        for key, value in data.items():
            if key in known:
                values[key] = value
            else:
                extra[key] = value
        cfg = cls(**values)
        cfg.extra = extra
        cfg.validate()
        return cfg

    def validate(self) -> None:
        if self.mode not in {"bot", "selfbot", "user"}:
            raise ValueError("mode must be 'bot', 'selfbot', or 'user'")
        if self.max_concurrency < 1 or self.max_concurrency > 50:
            raise ValueError("max_concurrency must be between 1 and 50")
        if self.selfbot_max_concurrency < 1 or self.selfbot_max_concurrency > 20:
            raise ValueError("selfbot_max_concurrency must be between 1 and 20")
        if self.bulk_delete_batch_size < 1 or self.bulk_delete_batch_size > 100:
            raise ValueError("bulk_delete_batch_size must be between 1 and 100")
        if self.log_level not in {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}:
            raise ValueError("invalid log_level")

    def max_workers_for_mode(self, mode: str) -> int:
        if mode in {"selfbot", "user"}:
            return min(self.max_concurrency, self.selfbot_max_concurrency)
        return self.max_concurrency

    def to_dict(self) -> dict[str, Any]:
        return {
            "mode": self.mode,
            "max_concurrency": self.max_concurrency,
            "default_dry_run": self.default_dry_run,
            "backup_dir": self.backup_dir,
            "log_level": self.log_level,
            "proxy": self.proxy,
            "abort_on_error": self.abort_on_error,
            "bulk_delete_batch_size": self.bulk_delete_batch_size,
            "selfbot_max_concurrency": self.selfbot_max_concurrency,
            **self.extra,
        }
