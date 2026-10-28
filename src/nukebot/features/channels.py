"""Channel nuke and management features."""

from __future__ import annotations

import asyncio
from typing import Any

import discord

from nukebot.core.dryrun import DryRunContext
from nukebot.core.rate_limit import RateLimiter
from nukebot.core.templates import render_template
from nukebot.features.common import Context, Result

CHANNEL_TYPES = {
    "text": "text",
    "voice": "voice",
    "category": "category",
    "forum": "forum",
    "announcement": "announcement",
    "stage": "stage",
}


def _match(channel: Any, name_filter: str | None = None, type_filter: str | None = None) -> bool:
    if type_filter and str(channel.type).lower() != type_filter.lower():
        return False
    if name_filter and name_filter.lower() not in channel.name.lower():
        return False
    return True


async def list_channels(ctx: Context, name_filter: str | None = None, type_filter: str | None = None) -> list[Any]:
    return [c for c in ctx.guild.channels if _match(c, name_filter, type_filter)]


async def create_channels(
    ctx: Context,
    channel_type: str,
    name_template: str,
    count: int,
    category_id: int | None = None,
    topic: str | None = None,
    nsfw: bool = False,
    slowmode_delay: int = 0,
) -> Result:
    result = Result(action="create_channels")
    category = ctx.guild.get_channel(category_id) if category_id else None
    if ctx.dry_run.enabled:
        ctx.dry_run.record("create_channel", channel_type, count)
        result.success = count
        return result

    for i in range(1, count + 1):
        name = render_template(name_template, i, {"guild": ctx.guild.name})
        try:
            if channel_type == "text":
                await ctx.rate_limiter.run(
                    lambda name=name: ctx.guild.create_text_channel(
                        name=name, category=category, topic=topic, nsfw=nsfw, slowmode_delay=slowmode_delay
                    ),
                    "create_text_channel",
                )
            elif channel_type == "voice":
                await ctx.rate_limiter.run(
                    lambda name=name: ctx.guild.create_voice_channel(name=name, category=category),
                    "create_voice_channel",
                )
            elif channel_type == "category":
                await ctx.rate_limiter.run(
                    lambda name=name: ctx.guild.create_category(name=name, position=i),
                    "create_category",
                )
            elif channel_type == "forum":
                await ctx.rate_limiter.run(
                    lambda name=name: ctx.guild.create_forum(name=name, category=category, topic=topic),
                    "create_forum",
                )
            elif channel_type == "announcement":
                create = getattr(ctx.guild, "create_news_channel", None)
                if create is None:
                    await ctx.rate_limiter.run(
                        lambda name=name: ctx.guild.create_text_channel(name=name, category=category, news=True),
                        "create_announcement",
                    )
                else:
                    await ctx.rate_limiter.run(
                        lambda name=name: create(name=name, category=category, topic=topic),
                        "create_announcement",
                    )
            elif channel_type == "stage":
                await ctx.rate_limiter.run(
                    lambda name=name: ctx.guild.create_stage_channel(name=name, category=category),
                    "create_stage_channel",
                )
            else:
                raise ValueError(f"Unknown channel type: {channel_type}")
            result.success += 1
        except Exception as exc:  # noqa: BLE001
            result.add_error(f"create {name}: {exc}")
    return result


async def delete_channels(ctx: Context, channels: list[Any]) -> Result:
    result = Result(action="delete_channels")
    if ctx.dry_run.enabled:
        ctx.dry_run.record("delete_channel", "channel", len(channels))
        result.success = len(channels)
        return result
    for channel in channels:
        try:
            await ctx.rate_limiter.run(lambda channel=channel: channel.delete(), "delete_channel")
            result.success += 1
        except Exception as exc:  # noqa: BLE001
            result.add_error(f"delete {getattr(channel, 'name', channel.id)}: {exc}")
    return result


async def rename_channels(ctx: Context, channels: list[Any], template: str) -> Result:
    result = Result(action="rename_channels")
    if ctx.dry_run.enabled:
        ctx.dry_run.record("rename_channel", "channel", len(channels))
        result.success = len(channels)
        return result
    for index, channel in enumerate(channels, start=1):
        name = render_template(template, index, {"name": channel.name, "guild": ctx.guild.name})
        try:
            await ctx.rate_limiter.run(lambda channel=channel, name=name: channel.edit(name=name), "rename_channel")
            result.success += 1
        except Exception as exc:  # noqa: BLE001
            result.add_error(f"rename {channel.id}: {exc}")
    return result


async def clone_channel(ctx: Context, channel: Any, name: str | None = None) -> Result:
    result = Result(action="clone_channel")
    if ctx.dry_run.enabled:
        ctx.dry_run.record("clone_channel", getattr(channel, "name", str(channel.id)), 1)
        result.success = 1
        return result
    try:
        await ctx.rate_limiter.run(lambda: channel.clone(name=name), "clone_channel")
        result.success = 1
    except Exception as exc:  # noqa: BLE001
        result.add_error(f"clone {channel.id}: {exc}")
    return result


async def lock_channels(ctx: Context, channels: list[Any], locked: bool = True) -> Result:
    result = Result(action="lock_channels" if locked else "unlock_channels")
    if ctx.dry_run.enabled:
        ctx.dry_run.record("lock_channel", "channel", len(channels))
        result.success = len(channels)
        return result
    for channel in channels:
        try:
            overwrite = channel.overwrites_for(ctx.guild.default_role)
            overwrite.send_messages = False if locked else None
            overwrite.connect = False if locked else None
            await ctx.rate_limiter.run(
                lambda channel=channel, overwrite=overwrite: channel.set_permissions(
                    ctx.guild.default_role, overwrite=overwrite
                ),
                "lock_channel",
            )
            result.success += 1
        except Exception as exc:  # noqa: BLE001
            result.add_error(f"lock {channel.id}: {exc}")
    return result


async def set_slowmode(ctx: Context, channels: list[Any], delay: int) -> Result:
    result = Result(action="set_slowmode")
    if ctx.dry_run.enabled:
        ctx.dry_run.record("set_slowmode", "channel", len(channels))
        result.success = len(channels)
        return result
    for channel in channels:
        try:
            await ctx.rate_limiter.run(lambda channel=channel: channel.edit(slowmode_delay=delay), "set_slowmode")
            result.success += 1
        except Exception as exc:  # noqa: BLE001
            result.add_error(f"slowmode {channel.id}: {exc}")
    return result


async def spam_topic(ctx: Context, channels: list[Any], topic: str, count: int = 1) -> Result:
    result = Result(action="spam_topic")
    if ctx.dry_run.enabled:
        ctx.dry_run.record("spam_topic", "channel", len(channels) * count)
        result.success = len(channels) * count
        return result
    for _ in range(count):
        for channel in channels:
            try:
                await ctx.rate_limiter.run(lambda channel=channel: channel.edit(topic=topic), "spam_topic")
                result.success += 1
            except Exception as exc:  # noqa: BLE001
                result.add_error(f"topic {channel.id}: {exc}")
    return result


async def nuke_channel(ctx: Context, channel: Any) -> Result:
    result = Result(action="nuke_channel")
    if ctx.dry_run.enabled:
        ctx.dry_run.record("nuke_channel", getattr(channel, "name", str(channel.id)), 1)
        result.success = 1
        return result
    try:
        position = channel.position
        category = channel.category
        name = channel.name
        topic = getattr(channel, "topic", None)
        await ctx.rate_limiter.run(lambda: channel.delete(), "delete_channel")
        await ctx.rate_limiter.run(
            lambda: ctx.guild.create_text_channel(name=name, category=category, topic=topic, position=position),
            "recreate_channel",
        )
        result.success = 1
    except Exception as exc:  # noqa: BLE001
        result.add_error(f"nuke {channel.id}: {exc}")
    return result
