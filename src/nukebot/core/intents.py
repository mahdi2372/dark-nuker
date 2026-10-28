"""Intent helpers for bot and selfbot modes."""

from __future__ import annotations

import discord

from nukebot.storage.logging import get_logger

log = get_logger("intents")


def make_intents(mode: str) -> discord.Intents:
    if mode in {"selfbot", "user"}:
        # User accounts receive the full intent set.
        return discord.Intents.all()
    intents = discord.Intents.default()
    intents.members = True
    intents.message_content = True
    intents.guilds = True
    intents.guild_messages = True
    intents.guild_reactions = True
    intents.voice_states = True
    intents.emojis_and_stickers = True
    return intents


def privileged_intent_warning(mode: str) -> str | None:
    if mode == "bot":
        return (
            "Bot mode requires privileged intents (members, message_content) enabled "
            "in the Discord Developer Portal."
        )
    return None
