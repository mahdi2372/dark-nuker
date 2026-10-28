"""Prompt helpers for the interactive CLI."""

from __future__ import annotations

from nukebot.ui.console import ask, confirm


async def ask_int(prompt: str, default: int | None = None) -> int:
    value = ask(prompt, str(default) if default is not None else None)
    return int(value)


async def ask_float(prompt: str, default: float | None = None) -> float:
    value = ask(prompt, str(default) if default is not None else None)
    return float(value)


async def ask_choice(prompt: str, choices: list[str], default: str | None = None) -> str:
    rendered = ", ".join(choices)
    value = ask(f"{prompt} [{rendered}]", default)
    if value not in choices:
        raise ValueError(f"Invalid choice: {value}")
    return value


def parse_id_list(value: str) -> list[int]:
    return [int(part.strip()) for part in value.split(",") if part.strip()]


def parse_str_list(value: str) -> list[str]:
    return [part.strip() for part in value.split(",") if part.strip()]
