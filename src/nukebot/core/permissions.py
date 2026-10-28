"""Permission checks for bot and selfbot modes."""

from __future__ import annotations

from typing import Any

import discord

from nukebot.storage.logging import get_logger

log = get_logger("permissions")


def is_selfbot(mode: str) -> bool:
    return mode in {"selfbot", "user"}


def guild_permissions(client: Any, guild: discord.Guild) -> discord.Permissions:
    if is_selfbot(client.mode if hasattr(client, "mode") else mode_from_client(client)):
        return discord.Permissions.all()
    member = guild.me
    if member is None:
        return discord.Permissions.none()
    return member.guild_permissions


def mode_from_client(client: Any) -> str:
    return getattr(client, "mode", "bot")


def has_permission(client: Any, guild: discord.Guild, name: str) -> bool:
    if is_selfbot(mode_from_client(client)):
        return True
    perms = guild_permissions(client, guild)
    return getattr(perms, name, False)


def require_permission(client: Any, guild: discord.Guild, name: str) -> None:
    if not has_permission(client, guild, name):
        raise PermissionError(f"Missing required permission: {name}")


def permission_summary(client: Any, guild: discord.Guild) -> dict[str, bool]:
    names = [
        "administrator",
        "manage_guild",
        "manage_channels",
        "manage_roles",
        "kick_members",
        "ban_members",
        "moderate_members",
        "manage_messages",
        "manage_webhooks",
        "manage_emojis_and_stickers",
        "move_members",
        "mute_members",
        "deafen_members",
    ]
    if is_selfbot(mode_from_client(client)):
        return {name: True for name in names}
    perms = guild_permissions(client, guild)
    return {name: getattr(perms, name, False) for name in names}
