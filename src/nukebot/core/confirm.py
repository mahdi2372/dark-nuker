"""Destructive action confirmation helpers."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class ConfirmationResult:
    approved: bool
    reason: str = ""


def summarize(items: list[str] | int, noun: str) -> str:
    count = len(items) if isinstance(items, list) else int(items)
    return f"{count} {noun}"


async def confirm_destructive(
    input_func,
    output_func,
    guild_name: str,
    action: str,
    affected_count: int,
    affected_noun: str,
) -> ConfirmationResult:
    output_func(f"Action: {action}")
    output_func(f"Affected: {affected_count} {affected_noun}")
    output_func(f"Guild: {guild_name}")
    answer = await input_func(f"Type the guild name '{guild_name}' to continue: ")
    if answer.strip() != guild_name:
        return ConfirmationResult(False, "guild name mismatch")
    answer = await input_func("Type CONFIRM to execute: ")
    if answer.strip() != "CONFIRM":
        return ConfirmationResult(False, "confirmation keyword mismatch")
    return ConfirmationResult(True)


def confirm_non_destructive(input_func, prompt: str) -> bool:
    answer = input_func(prompt)
    return str(answer).strip().lower() in {"y", "yes", "confirm"}
