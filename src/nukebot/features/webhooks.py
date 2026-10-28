"""Webhook management features."""

from __future__ import annotations

import discord

from nukebot.features.common import Context, Result


async def list_webhooks(ctx: Context, channel: Any | None = None) -> list[Any]:
    if channel is not None:
        return await channel.webhooks()
    result_list = []
    for ch in ctx.guild.text_channels:
        try:
            result_list.extend(await ch.webhooks())
        except Exception:
            continue
    return result_list


async def create_webhooks(ctx: Context, channel: Any, names: list[str]) -> Result:
    result = Result(action="create_webhooks")
    if ctx.dry_run.enabled:
        ctx.dry_run.record("create_webhook", getattr(channel, "name", str(channel.id)), len(names))
        result.success = len(names)
        return result
    for name in names:
        try:
            await ctx.rate_limiter.run(lambda name=name: channel.create_webhook(name=name), "create_webhook")
            result.success += 1
        except Exception as exc:  # noqa: BLE001
            result.add_error(f"create_webhook {name}: {exc}")
    return result


async def delete_webhooks(ctx: Context, webhooks: list[Any]) -> Result:
    result = Result(action="delete_webhooks")
    if ctx.dry_run.enabled:
        ctx.dry_run.record("delete_webhook", "webhook", len(webhooks))
        result.success = len(webhooks)
        return result
    for webhook in webhooks:
        try:
            await ctx.rate_limiter.run(lambda webhook=webhook: webhook.delete(), "delete_webhook")
            result.success += 1
        except Exception as exc:  # noqa: BLE001
            result.add_error(f"delete_webhook {getattr(webhook, 'id', webhook)}: {exc}")
    return result
