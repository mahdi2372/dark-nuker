"""Emoji and sticker management features."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import discord

from nukebot.features.common import Context, Result


async def delete_emojis(ctx: Context, emojis: list[Any]) -> Result:
    result = Result(action="delete_emojis")
    if ctx.dry_run.enabled:
        ctx.dry_run.record("delete_emoji", "emoji", len(emojis))
        result.success = len(emojis)
        return result
    for emoji in emojis:
        try:
            await ctx.rate_limiter.run(lambda emoji=emoji: emoji.delete(), "delete_emoji")
            result.success += 1
        except Exception as exc:  # noqa: BLE001
            result.add_error(f"delete_emoji {getattr(emoji, 'id', emoji)}: {exc}")
    return result


async def create_emoji(ctx: Context, name: str, image_path_or_url: str) -> Result:
    result = Result(action="create_emoji")
    if ctx.dry_run.enabled:
        ctx.dry_run.record("create_emoji", name, 1)
        result.success = 1
        return result
    try:
        data = None
        p = Path(image_path_or_url)
        if p.exists():
            data = p.read_bytes()
        else:
            import aiohttp

            async with aiohttp.ClientSession() as session:
                async with session.get(image_path_or_url) as resp:
                    data = await resp.read()
        await ctx.rate_limiter.run(lambda: ctx.guild.create_custom_emoji(name=name, image=data), "create_emoji")
        result.success = 1
    except Exception as exc:  # noqa: BLE001
        result.add_error(f"create_emoji {name}: {exc}")
    return result


async def rename_emoji(ctx: Context, emoji: Any, name: str) -> Result:
    result = Result(action="rename_emoji")
    if ctx.dry_run.enabled:
        ctx.dry_run.record("rename_emoji", getattr(emoji, "name", str(emoji.id)), 1)
        result.success = 1
        return result
    try:
        await ctx.rate_limiter.run(lambda: emoji.edit(name=name), "rename_emoji")
        result.success = 1
    except Exception as exc:  # noqa: BLE001
        result.add_error(f"rename_emoji {emoji.id}: {exc}")
    return result


async def delete_stickers(ctx: Context, stickers: list[Any]) -> Result:
    result = Result(action="delete_stickers")
    if ctx.dry_run.enabled:
        ctx.dry_run.record("delete_sticker", "sticker", len(stickers))
        result.success = len(stickers)
        return result
    for sticker in stickers:
        try:
            await ctx.rate_limiter.run(lambda sticker=sticker: sticker.delete(), "delete_sticker")
            result.success += 1
        except Exception as exc: # noqa: BLE001
            result.add_error(f"delete_sticker {getattr(sticker, 'id', sticker)}: {exc}")
    return result


async def create_sticker(ctx: Context, name: str, image_path: str, description: str = "") -> Result:
    result = Result(action="create_sticker")
    if ctx.dry_run.enabled:
        ctx.dry_run.record("create_sticker", name, 1)
        result.success = 1
        return result
    try:
        p = Path(image_path)
        data = p.read_bytes()
        await ctx.rate_limiter.run(
            lambda: ctx.guild.create_sticker(name=name, description=description, file=discord.File(p)),
            "create_sticker",
        )
        result.success = 1
    except Exception as exc:  # noqa: BLE001
        result.add_error(f"create_sticker {name}: {exc}")
    return result
