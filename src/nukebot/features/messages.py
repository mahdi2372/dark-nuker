"""Message nuke and spam features."""

from __future__ import annotations

import asyncio

import discord

from nukebot.core.rate_limit import RateLimiter
from nukebot.core.templates import render_template
from nukebot.features.common import Context, Result


async def purge_channel(ctx: Context, channel: Any, limit: int = 1000, bot_only: bool = False) -> Result:
    result = Result(action="purge_channel")
    if ctx.dry_run.enabled:
        ctx.dry_run.record("purge", getattr(channel, "name", str(channel.id)), limit)
        result.success = limit
        return result

    deleted = 0
    try:
        if ctx.client.is_bot_mode if hasattr(ctx.client, "is_bot_mode") else False:
            def check(m):
                return True if not bot_only else m.author == ctx.client.user
            purged = await ctx.rate_limiter.run(lambda: channel.purge(limit=limit, check=check), "purge")
            deleted = len(purged) if purged else 0
        else:
            async for message in channel.history(limit=limit):
                if bot_only and message.author.id != ctx.client.user.id:
                    continue
                try:
                    await ctx.rate_limiter.run(lambda message=message: message.delete(), "delete_message")
                    deleted += 1
                except Exception:  # noqa: BLE001
                    result.failed += 1
    except Exception as exc:  # noqa: BLE001
        result.add_error(f"purge {channel.id}: {exc}")
    result.success = deleted
    return result


async def spam_messages(
    ctx: Context,
    channel: Any,
    content: str,
    count: int,
    delay: float = 0.5,
) -> Result:
    result = Result(action="spam_messages")
    if ctx.dry_run.enabled:
        ctx.dry_run.record("spam_message", getattr(channel, "name", str(channel.id)), count)
        result.success = count
        return result
    for i in range(count):
        text = render_template(content, i + 1, {"guild": ctx.guild.name})
        try:
            await ctx.rate_limiter.run(lambda text=text: channel.send(text), "send_message")
            result.success += 1
        except Exception as exc:  # noqa: BLE001
            result.add_error(f"send {i + 1}: {exc}")
        if delay:
            await asyncio.sleep(delay)
    return result


async def webhook_spam(
    ctx: Context,
    webhook: Any,
    content: str,
    count: int,
    delay: float = 0.5,
) -> Result:
    result = Result(action="webhook_spam")
    if ctx.dry_run.enabled:
        ctx.dry_run.record("webhook_spam", str(webhook.id), count)
        result.success = count
        return result
    for i in range(count):
        text = render_template(content, i + 1, {"guild": ctx.guild.name})
        try:
            await ctx.rate_limiter.run(lambda text=text: webhook.send(text), "webhook_send")
            result.success += 1
        except Exception as exc:  # noqa: BLE001
            result.add_error(f"webhook send {i + 1}: {exc}")
        if delay:
            await asyncio.sleep(delay)
    return result


async def pin_spam(ctx: Context, channel: Any, count: int = 10) -> Result:
    result = Result(action="pin_spam")
    if ctx.dry_run.enabled:
        ctx.dry_run.record("pin_spam", getattr(channel, "name", str(channel.id)), count)
        result.success = count
        return result
    pinned = 0
    async for message in channel.history(limit=count):
        try:
            await ctx.rate_limiter.run(lambda message=message: message.pin(), "pin")
            pinned += 1
        except Exception as exc:  # noqa: BLE001
            result.add_error(f"pin {message.id}: {exc}")
    result.success = pinned
    return result


async def react_spam(ctx: Context, channel: Any, emoji: str, count: int = 10) -> Result:
    result = Result(action="react_spam")
    if ctx.dry_run.enabled:
        ctx.dry_run.record("react_spam", getattr(channel, "name", str(channel.id)), count)
        result.success = count
        return result
    reacted = 0
    async for message in channel.history(limit=count):
        try:
            await ctx.rate_limiter.run(lambda message=message: message.add_reaction(emoji), "react")
            reacted += 1
        except Exception as exc:  # noqa: BLE001
            result.add_error(f"react {message.id}: {exc}")
    result.success = reacted
    return result


async def edit_own_messages(ctx: Context, channel: Any, new_content: str, limit: int = 50) -> Result:
    result = Result(action="edit_own_messages")
    if ctx.dry_run.enabled:
        ctx.dry_run.record("edit_own_messages", getattr(channel, "name", str(channel.id)), limit)
        result.success = limit
        return result
    edited = 0
    async for message in channel.history(limit=limit):
        if message.author.id != ctx.client.user.id:
            continue
        try:
            await ctx.rate_limiter.run(lambda message=message: message.edit(content=new_content), "edit_message")
            edited += 1
        except Exception as exc:  # noqa: BLE001
            result.add_error(f"edit {message.id}: {exc}")
    result.success = edited
    return result


async def delete_own_messages(ctx: Context, channel: Any, limit: int = 1000) -> Result:
    result = Result(action="delete_own_messages")
    if ctx.dry_run.enabled:
        ctx.dry_run.record("delete_own_messages", getattr(channel, "name", str(channel.id)), limit)
        result.success = limit
        return result
    deleted = 0
    async for message in channel.history(limit=limit):
        if message.author.id != ctx.client.user.id:
            continue
        try:
            await ctx.rate_limiter.run(lambda message=message: message.delete(), "delete_message")
            deleted += 1
        except Exception as exc:  # noqa: BLE001
            result.add_error(f"delete {message.id}: {exc}")
    result.success = deleted
    return result
