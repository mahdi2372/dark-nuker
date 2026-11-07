"""Intent helpers for bot and selfbot modes.

discord.py-self does not expose discord.Intents, so this module only keeps
compatibility helpers and returns None.
"""

from __future__ import annotations


def make_intents(mode: str):
    return None


def privileged_intent_warning(mode: str) -> str | None:
    if mode == "bot":
        return (
            "Bot mode requires the required privileged intents enabled in the "
            "Discord Developer Portal."
        )
    return None
