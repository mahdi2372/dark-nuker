"""Best-effort guild restore from JSON backup."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import discord

from nukebot.core.rate_limit import RateLimiter
from nukebot.storage.logging import get_logger

log = get_logger("restore")


async def restore_backup(
    guild: discord.Guild,
    backup_path: str | Path,
    rate_limiter: RateLimiter | None = None,
) -> dict[str, int]:
    rl = rate_limiter or RateLimiter(max_concurrency=3)
    data = json.loads(Path(backup_path).read_text(encoding="utf-8"))
    stats = {"roles": 0, "channels": 0, "webhooks": 0, "failures": 0}

    # Roles first, preserving approximate order from lowest to highest.
    role_map: dict[int, discord.Role] = {}
    for item in sorted(data.get("roles", []), key=lambda r: r.get("position", 0)):
        if item.get("name") == "@everyone":
            continue
        try:
            role = await rl.run(
                lambda item=item: guild.create_role(
                    name=item["name"],
                    color=discord.Color(item.get("color", 0)),
                    hoist=item.get("hoist", False),
                    mentionable=item.get("mentionable", False),
                    permissions=discord.Permissions(item.get("permissions", 0)),
                ),
                "restore_role",
            )
            role_map[item["id"]] = role
            stats["roles"] += 1
        except Exception as exc:  # noqa: BLE001
            stats["failures"] += 1
            log.warning("Failed to restore role %s: %s", item.get("name"), exc)

    # Channels.
    channel_map: dict[int, Any] = {}
    # Categories first.
    for item in data.get("channels", []):
        if item.get("type") not in {"category", "ChannelType.category"} and "category" not in str(item.get("type", "")).lower():
            continue
        try:
            channel = await rl.run(
                lambda item=item: guild.create_category(name=item["name"], position=item.get("position", 0)),
                "restore_category",
            )
            channel_map[item["id"]] = channel
            stats["channels"] += 1
        except Exception as exc:  # noqa: BLE001
            stats["failures"] += 1
            log.warning("Failed to restore category %s: %s", item.get("name"), exc)

    for item in data.get("channels", []):
        ctype = str(item.get("type", "")).lower()
        if "category" in ctype:
            continue
        category = None
        if item.get("category_id") in channel_map:
            category = channel_map[item["category_id"]]
        try:
            if "voice" in ctype:
                channel = await rl.run(
                    lambda item=item, category=category: guild.create_voice_channel(
                        name=item["name"],
                        category=category,
                        bitrate=item.get("bitrate") or 64000,
                        user_limit=item.get("user_limit") or 0,
                        position=item.get("position", 0),
                    ),
                    "restore_voice",
                )
            elif "forum" in ctype:
                channel = await rl.run(
                    lambda item=item, category=category: guild.create_forum(
                        name=item["name"],
                        category=category,
                        topic=item.get("topic"),
                        position=item.get("position", 0),
                    ),
                    "restore_forum",
                )
            else:
                channel = await rl.run(
                    lambda item=item, category=category: guild.create_text_channel(
                        name=item["name"],
                        category=category,
                        topic=item.get("topic"),
                        nsfw=item.get("nsfw", False),
                        slowmode_delay=item.get("slowmode_delay", 0),
                        position=item.get("position", 0),
                    ),
                    "restore_text",
                )
            channel_map[item["id"]] = channel
            stats["channels"] += 1
        except Exception as exc:  # noqa: BLE001
            stats["failures"] += 1
            log.warning("Failed to restore channel %s: %s", item.get("name"), exc)

    # Webhooks best-effort.
    for item in data.get("webhooks", []):
        channel_id = item.get("channel_id")
        channel = channel_map.get(channel_id) if channel_id else None
        if channel is None:
            continue
        try:
            await rl.run(lambda channel=channel, item=item: channel.create_webhook(name=item.get("name", "restored")), "restore_webhook")
            stats["webhooks"] += 1
        except Exception as exc:  # noqa: BLE001
            stats["failures"] += 1
            log.warning("Failed to restore webhook %s: %s", item.get("name"), exc)

    return stats
