"""Thread and forum management features."""

from __future__ import annotations

import discord

from nukebot.features.common import Context, Result


async def create_threads(ctx: Context, channel: Any, name_template: str, count: int) -> Result:
    result = Result(action="create_threads")
    if ctx.dry_run.enabled:
        ctx.dry_run.record("create_thread", getattr(channel, "name", str(channel.id)), count)
        result.success = count
        return result
    for i in range(1, count + 1):
        name = name_template.replace("{i}", str(i))
        try:
            await ctx.rate_limiter.run(lambda name=name: channel.create_thread(name=name), "create_thread")
            result.success += 1
        except Exception as exc:  # noqa: BLE001
            result.add_error(f"create_thread {i}: {exc}")
    return result


async def archive_threads(ctx: Context, threads: list[Any]) -> Result:
    result = Result(action="archive_threads")
    if ctx.dry_run.enabled:
        ctx.dry_run.record("archive_thread", "thread", len(threads))
        result.success = len(threads)
        return result
    for thread in threads:
        try:
            await ctx.rate_limiter.run(lambda thread=thread: thread.edit(archived=True), "archive_thread")
            result.success += 1
        except Exception as exc:  # noqa: BLE001
            result.add_error(f"archive_thread {getattr(thread, 'id', thread)}: {exc}")
    return result


async def delete_threads(ctx: Context, threads: list[Any]) -> Result:
    result = Result(action="delete_threads")
    if ctx.dry_run.enabled:
        ctx.dry_run.record("delete_thread", "thread", len(threads))
        result.success = len(threads)
        return result
    for thread in threads:
        try:
            await ctx.rate_limiter.run(lambda thread=thread: thread.delete(), "delete_thread")
            result.success += 1
        except Exception as exc:  # noqa: BLE001
            result.add_error(f"delete_thread {getattr(thread, 'id', thread)}: {exc}")
    return result
