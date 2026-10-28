"""Guild backup creation."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import discord

from nukebot.storage.logging import get_logger

log = get_logger("backup")


def _channel_type_name(channel: Any) -> str:
    return str(getattr(channel, "type", "unknown"))


def _overwrites(channel: Any) -> list[dict[str, Any]]:
    result = []
    for target, overwrite in getattr(channel, "overwrites", {}).items():
        result.append(
            {
                "target_id": getattr(target, "id", None),
                "target_type": "role" if isinstance(target, discord.Role) else "member",
                "allow": overwrite.pair()[0].value if hasattr(overwrite, "pair") else int(overwrite.allow),
                "deny": overwrite.pair()[1].value if hasattr(overwrite, "pair") else int(overwrite.deny),
            }
        )
    return result


def serialize_channel(channel: Any) -> dict[str, Any]:
    return {
        "id": channel.id,
        "name": channel.name,
        "type": _channel_type_name(channel),
        "position": getattr(channel, "position", 0),
        "category_id": getattr(channel, "category_id", None),
        "topic": getattr(channel, "topic", None),
        "nsfw": getattr(channel, "nsfw", False),
        "slowmode_delay": getattr(channel, "slowmode_delay", 0),
        "bitrate": getattr(channel, "bitrate", None),
        "user_limit": getattr(channel, "user_limit", None),
        "overwrites": _overwrites(channel),
    }


def serialize_role(role: discord.Role) -> dict[str, Any]:
    return {
        "id": role.id,
        "name": role.name,
        "color": int(role.color),
        "hoist": role.hoist,
        "mentionable": role.mentionable,
        "permissions": role.permissions.value,
        "position": role.position,
    }


def serialize_emoji(emoji: Any) -> dict[str, Any]:
    return {
        "id": emoji.id,
        "name": emoji.name,
        "animated": getattr(emoji, "animated", False),
        "url": str(getattr(emoji, "url", "")),
    }


def serialize_sticker(sticker: Any) -> dict[str, Any]:
    return {
        "id": sticker.id,
        "name": sticker.name,
        "description": getattr(sticker, "description", None),
        "format": str(getattr(sticker, "format", "")),
        "url": str(getattr(sticker, "url", "")),
    }


def serialize_webhook(webhook: Any) -> dict[str, Any]:
    return {
        "id": webhook.id,
        "name": webhook.name,
        "channel_id": getattr(webhook, "channel_id", None),
        "url": getattr(webhook, "url", None),
    }


async def create_backup(guild: discord.Guild, backup_dir: str = "backups") -> Path:
    root = Path(backup_dir) / str(guild.id)
    root.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    path = root / f"{timestamp}.json"

    data = {
        "version": 1,
        "guild_id": guild.id,
        "guild_name": guild.name,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "channels": [serialize_channel(c) for c in guild.channels],
        "roles": [serialize_role(r) for r in guild.roles],
        "emojis": [serialize_emoji(e) for e in guild.emojis],
        "stickers": [serialize_sticker(s) for s in guild.stickers],
        "webhooks": [],
        "metadata": {
            "verification_level": str(guild.verification_level),
            "default_notifications": str(guild.default_notifications),
            "explicit_content_filter": str(guild.explicit_content_filter),
            "afk_timeout": guild.afk_timeout,
            "afk_channel_id": getattr(guild.afk_channel, "id", None),
            "system_channel_id": getattr(guild.system_channel, "id", None),
            "rules_channel_id": getattr(guild.rules_channel, "id", None),
            "public_updates_channel_id": getattr(guild.public_updates_channel, "id", None),
        },
    }

    for channel in guild.text_channels:
        try:
            data["webhooks"].extend(serialize_webhook(w) for w in await channel.webhooks())
        except Exception as exc:  # noqa: BLE001
            log.warning("Could not list webhooks for %s: %s", channel.id, exc)

    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    log.info("Backup created: %s", path)
    return path
