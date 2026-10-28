"""Interactive CLI menu."""

from __future__ import annotations

import asyncio
from pathlib import Path

from nukebot.core.client import create_client, close_client
from nukebot.core.dryrun import DryRunContext
from nukebot.core.intents import make_intents
from nukebot.core.rate_limit import RateLimiter
from nukebot.features.common import Context
from nukebot.features import channels, roles, members, messages, server, webhooks, emojis, threads, integrations, raid, utility, nuke_all, advanced
from nukebot.storage.config import Config
from nukebot.storage.secrets import get_token, set_token, save_profile, list_profiles, delete_profile, load_dotenv
from nukebot.ui.console import (
    ask,
    confirm,
    console,
    info,
    success,
    warning,
    error,
    render_result,
    render_guilds,
    render_channels,
    render_roles,
    banner,
    menu,
)
from nukebot.cli.prompts import parse_id_list, parse_str_list

BANNER = "DARK NUKER — ultra advanced | Developed by Mahdi"


class AccountSwitched(Exception):
    """Raised when the active account/token changes mid-session."""
    pass


def _channels_by_ids(guild, ids):
    if not ids:
        return list(guild.channels)
    return [guild.get_channel(i) for i in ids if guild.get_channel(i)]


def _roles_by_ids(guild, ids):
    if not ids:
        return [r for r in guild.roles if r.name != "@everyone"]
    return [guild.get_role(i) for i in ids if guild.get_role(i)]


async def _login(config: Config):
    load_dotenv()
    mode = ask("Mode (bot/selfbot)", default=config.mode)
    if mode not in {"bot", "selfbot", "user"}:
        mode = "bot"
    profiles = list_profiles(mode)
    if profiles:
        console.print("Saved profiles: " + ", ".join(profiles))
    profile = ask("Token profile (name or 'new')", default=profiles[0] if profiles else "default")
    if profile.lower() == "new":
        profile = ask("New profile name", default="default")
    token = get_token(mode, profile)
    if not token:
        token = ask("Token")
    if token and confirm("Save token to this profile?", default=True):
        if save_profile(mode, profile, token):
            success(f"Token saved to profile '{profile}'")
        else:
            warning("Could not save token (keyring unavailable)")
    intents = make_intents(mode)
    client = await create_client(mode, token, intents, proxy=getattr(config, "proxy", None))
    mode = client.mode
    return client, mode


async def _select_guild(client):
    render_guilds(client.guilds)
    while True:
        raw = ask("Guild ID (0 to exit)")
        if raw == "0":
            return None
        try:
            guild = client.get_guild(int(raw))
            if guild is None:
                guild = await client.fetch_guild(int(raw))
            return guild
        except Exception as exc:  # noqa: BLE001
            error(str(exc))


async def _channel_ids_prompt(guild, prompt="Channel IDs (comma, blank=all)"):
    raw = ask(prompt)
    if not raw.strip():
        return [c.id for c in guild.channels]
    return parse_id_list(raw)


async def _role_ids_prompt(guild, prompt="Role IDs (comma, blank=all non-default)"):
    raw = ask(prompt)
    if not raw.strip():
        return [r.id for r in guild.roles if r.name != "@everyone"]
    return parse_id_list(raw)


async def run_interactive(config: Config) -> int:
    banner()
    console.print(f"[bold red]{BANNER}[/bold red]")
    client = None
    mode = config.mode
    dry_run = DryRunContext(enabled=config.default_dry_run)
    rate_limiter = None

    try:
        while True:
            if client is None:
                menu("DARK NUKER — Main Menu", [
                    ("1", "Login / Add token"),
                    ("0", "Exit"),
                ])
                choice = ask("Select", default="1")
                if choice == "0":
                    break
                if choice == "1":
                    client, mode = await _login(config)
                    rate_limiter = RateLimiter(max_concurrency=config.max_workers_for_mode(mode))
                    success(f"Logged in: {client.describe()}")
                continue

            menu("DARK NUKER — Main Menu", [
                ("1", "Switch account / Add token"),
                ("2", "Select guild"),
                ("3", "Settings"),
                ("0", "Logout / Exit"),
            ])
            choice = ask("Select", default="2")
            if choice == "0":
                await close_client(client)
                client = None
                rate_limiter = None
                continue
            if choice == "1":
                await close_client(client)
                client, mode = await _login(config)
                rate_limiter = RateLimiter(max_concurrency=config.max_workers_for_mode(mode))
                success(f"Logged in: {client.describe()}")
                continue
            if choice == "2":
                guild = await _select_guild(client)
                if guild is None:
                    continue
                ctx = Context(
                    client=client,
                    guild=guild,
                    rate_limiter=rate_limiter,
                    dry_run=dry_run,
                    mode=mode,
                    logger=None,
                    config=config,
                )
                await _guild_menu(ctx)
                client = ctx.client
                mode = ctx.mode
                rate_limiter = ctx.rate_limiter
                dry_run = ctx.dry_run
                continue
            if choice == "3":
                # Settings require a guild; use a temporary context with the first guild if available.
                if client.guilds:
                    ctx = Context(
                        client=client,
                        guild=client.guilds[0],
                        rate_limiter=rate_limiter,
                        dry_run=dry_run,
                        mode=mode,
                        logger=None,
                        config=config,
                    )
                    try:
                        await _settings_menu(ctx)
                    except AccountSwitched:
                        client = ctx.client
                        mode = ctx.mode
                        rate_limiter = ctx.rate_limiter
                        dry_run = ctx.dry_run
                else:
                    warning("No guilds available")
                continue
    finally:
        if client is not None:
            await close_client(client)
    return 0


async def _guild_menu(ctx: Context) -> None:
    while True:
        info(f"Guild: {ctx.guild.name} | dry_run={ctx.dry_run.enabled}")
        menu("Guild Menu", [
            ("1", "Channels"),
            ("2", "Roles"),
            ("3", "Members"),
            ("4", "Messages"),
            ("5", "Server"),
            ("6", "Webhooks"),
            ("7", "Emojis/Stickers"),
            ("8", "Threads"),
            ("9", "Integrations"),
            ("10", "Raid/Utility"),
            ("11", "Settings"),
            ("12", "Advanced"),
            ("0", "Back"),
        ])
        choice = ask("Select", default="0")
        if choice == "0":
            return
        if choice == "1":
            await _channels_menu(ctx)
        elif choice == "2":
            await _roles_menu(ctx)
        elif choice == "3":
            await _members_menu(ctx)
        elif choice == "4":
            await _messages_menu(ctx)
        elif choice == "5":
            await _server_menu(ctx)
        elif choice == "6":
            await _webhooks_menu(ctx)
        elif choice == "7":
            await _emojis_menu(ctx)
        elif choice == "8":
            await _threads_menu(ctx)
        elif choice == "9":
            await _integrations_menu(ctx)
        elif choice == "10":
            await _raid_menu(ctx)
        elif choice == "11":
            try:
                await _settings_menu(ctx)
            except AccountSwitched:
                return
        elif choice == "12":
            await _advanced_menu(ctx)


async def _channels_menu(ctx: Context) -> None:
    while True:
        menu("Channels", [
            ("1", "List channels"),
            ("2", "Create channels"),
            ("3", "Delete channels"),
            ("4", "Rename channels"),
            ("5", "Clone channel"),
            ("6", "Lock/unlock"),
            ("7", "Slowmode"),
            ("8", "Spam topic"),
            ("9", "Nuke channel"),
            ("0", "Back"),
        ])
        choice = ask("Select", default="0")
        if choice == "0":
            return
        try:
            if choice == "1":
                render_channels(ctx.guild.channels)
            elif choice == "2":
                ctype = ask("Type (text/voice/category/forum/announcement/stage)", default="text")
                template = ask("Name template", default="nuke-{i}")
                count = int(ask("Count", default="10"))
                result = await channels.create_channels(ctx, ctype, template, count)
                render_result(result)
            elif choice == "3":
                ids = await _channel_ids_prompt(ctx.guild)
                chans = _channels_by_ids(ctx.guild, ids)
                if not await _confirm_action(ctx, "delete_channels", len(chans)):
                    continue
                result = await channels.delete_channels(ctx, chans)
                render_result(result)
            elif choice == "4":
                ids = await _channel_ids_prompt(ctx.guild)
                chans = _channels_by_ids(ctx.guild, ids)
                template = ask("Name template", default="nuked-{i}")
                result = await channels.rename_channels(ctx, chans, template)
                render_result(result)
            elif choice == "5":
                cid = int(ask("Channel ID"))
                channel = ctx.guild.get_channel(cid)
                name = ask("New name (blank=same)", default="")
                result = await channels.clone_channel(ctx, channel, name or None)
                render_result(result)
            elif choice == "6":
                ids = await _channel_ids_prompt(ctx.guild)
                chans = _channels_by_ids(ctx.guild, ids)
                locked = confirm("Lock? (no=unlock)")
                result = await channels.lock_channels(ctx, chans, locked=locked)
                render_result(result)
            elif choice == "7":
                ids = await _channel_ids_prompt(ctx.guild)
                chans = _channels_by_ids(ctx.guild, ids)
                delay = int(ask("Slowmode seconds", default="0"))
                result = await channels.set_slowmode(ctx, chans, delay)
                render_result(result)
            elif choice == "8":
                ids = await _channel_ids_prompt(ctx.guild)
                chans = _channels_by_ids(ctx.guild, ids)
                topic = ask("Topic")
                count = int(ask("Times", default="1"))
                result = await channels.spam_topic(ctx, chans, topic, count)
                render_result(result)
            elif choice == "9":
                cid = int(ask("Channel ID"))
                channel = ctx.guild.get_channel(cid)
                if not await _confirm_action(ctx, "nuke_channel", 1):
                    continue
                result = await channels.nuke_channel(ctx, channel)
                render_result(result)
        except Exception as exc:  # noqa: BLE001
            error(str(exc))


async def _confirm_action(ctx: Context, action: str, count: int) -> bool:
    from nukebot.core.confirm import confirm_destructive

    if ctx.dry_run.enabled:
        return True
    conf = await confirm_destructive(
        lambda prompt: asyncio.to_thread(input, prompt),
        lambda message: print(message),
        ctx.guild.name,
        action,
        count,
        "objects",
    )
    if not conf.approved:
        warning(conf.reason)
        return False
    return True


async def _roles_menu(ctx: Context) -> None:
    while True:
        menu("Roles", [
            ("1", "List roles"),
            ("2", "Create roles"),
            ("3", "Delete roles"),
            ("4", "Rename roles"),
            ("5", "Mass assign/remove"),
            ("6", "Permission nuke"),
            ("7", "Color cycle"),
            ("8", "Hoist toggle"),
            ("0", "Back"),
        ])
        choice = ask("Select", default="0")
        if choice == "0":
            return
        try:
            if choice == "1":
                render_roles(ctx.guild.roles)
            elif choice == "2":
                template = ask("Name template", default="role-{i}")
                count = int(ask("Count", default="10"))
                admin = confirm("Administrator permissions?", default=False)
                result = await roles.create_roles(ctx, template, count, administrator=admin)
                render_result(result)
            elif choice == "3":
                ids = await _role_ids_prompt(ctx.guild)
                selected = _roles_by_ids(ctx.guild, ids)
                if not await _confirm_action(ctx, "delete_roles", len(selected)):
                    continue
                result = await roles.delete_roles(ctx, selected)
                render_result(result)
            elif choice == "4":
                ids = await _role_ids_prompt(ctx.guild)
                selected = _roles_by_ids(ctx.guild, ids)
                template = ask("Name template", default="role-{i}")
                result = await roles.rename_roles(ctx, selected, template)
                render_result(result)
            elif choice == "5":
                rid = int(ask("Role ID"))
                role = ctx.guild.get_role(rid)
                ids_raw = ask("Member IDs (comma, blank=all non-bots)")
                if ids_raw.strip():
                    member_ids = parse_id_list(ids_raw)
                    members = [ctx.guild.get_member(i) for i in member_ids]
                    members = [m for m in members if m]
                else:
                    members = [m for m in ctx.guild.members if not m.bot]
                remove = confirm("Remove instead of assign?", default=False)
                result = await roles.mass_assign_role(ctx, role, members, remove=remove)
                render_result(result)
            elif choice == "6":
                rid_raw = ask("Role ID (blank=@everyone)", default="")
                role = ctx.guild.get_role(int(rid_raw)) if rid_raw.strip() else None
                if not await _confirm_action(ctx, "permission_nuke", 1):
                    continue
                result = await roles.permission_nuke(ctx, role)
                render_result(result)
            elif choice == "7":
                rid = int(ask("Role ID"))
                role = ctx.guild.get_role(rid)
                colors = parse_id_list(ask("Colors hex ints comma", default="16711680,65280,255"))
                result = await roles.role_color_cycle(ctx, role, colors)
                render_result(result)
            elif choice == "8":
                ids = await _role_ids_prompt(ctx.guild)
                selected = _roles_by_ids(ctx.guild, ids)
                hoist = confirm("Hoist?", default=True)
                result = await roles.hoist_toggle(ctx, selected, hoist)
                render_result(result)
        except Exception as exc:  # noqa: BLE001
            error(str(exc))


async def _members_menu(ctx: Context) -> None:
    while True:
        menu("Members", [
            ("1", "Mass ban"),
            ("2", "Mass kick"),
            ("3", "Mass timeout"),
            ("4", "Mass unban"),
            ("5", "Mass nickname"),
            ("6", "Mass move to voice"),
            ("7", "Mass voice mute/deafen"),
            ("8", "Mass DM"),
            ("9", "Scrape member IDs"),
            ("10", "Prune inactive"),
            ("11", "Join invite"),
            ("12", "Leave guild"),
            ("13", "Mass ID operations"),
            ("0", "Back"),
        ])
        choice = ask("Select", default="0")
        if choice == "0":
            return
        try:
            if choice == "1":
                ids_raw = ask("Member IDs (blank=all non-bots)", default="")
                if ids_raw.strip():
                    members = [ctx.guild.get_member(i) for i in parse_id_list(ids_raw)]
                    members = [m for m in members if m]
                else:
                    members = [m for m in ctx.guild.members if not m.bot]
                reason = ask("Reason", default="Nuked")
                days = int(ask("Delete message days 0-7", default="0"))
                if not await _confirm_action(ctx, "mass_ban", len(members)):
                    continue
                result = await members.mass_ban(ctx, members, reason=reason, delete_message_days=days)
                render_result(result)
            elif choice == "2":
                ids_raw = ask("Member IDs (blank=all non-bots)", default="")
                if ids_raw.strip():
                    members = [ctx.guild.get_member(i) for i in parse_id_list(ids_raw)]
                    members = [m for m in members if m]
                else:
                    members = [m for m in ctx.guild.members if not m.bot]
                reason = ask("Reason", default="Nuked")
                if not await _confirm_action(ctx, "mass_kick", len(members)):
                    continue
                result = await members.mass_kick(ctx, members, reason=reason)
                render_result(result)
            elif choice == "3":
                ids_raw = ask("Member IDs (blank=all non-bots)", default="")
                if ids_raw.strip():
                    members = [ctx.guild.get_member(i) for i in parse_id_list(ids_raw)]
                    members = [m for m in members if m]
                else:
                    members = [m for m in ctx.guild.members if not m.bot]
                seconds = int(ask("Timeout seconds", default="3600"))
                result = await members.mass_timeout(ctx, members, seconds)
                render_result(result)
            elif choice == "4":
                ids = parse_id_list(ask("User IDs comma"))
                result = await members.mass_unban(ctx, ids)
                render_result(result)
            elif choice == "5":
                ids_raw = ask("Member IDs (blank=all non-bots)", default="")
                if ids_raw.strip():
                    members = [ctx.guild.get_member(i) for i in parse_id_list(ids_raw)]
                    members = [m for m in members if m]
                else:
                    members = [m for m in ctx.guild.members if not m.bot]
                template = ask("Nickname template", default="nuked-{i}")
                result = await members.mass_nickname(ctx, members, template)
                render_result(result)
            elif choice == "6":
                cid = int(ask("Voice channel ID"))
                channel = ctx.guild.get_channel(cid)
                ids_raw = ask("Member IDs (blank=all non-bots in voice)", default="")
                if ids_raw.strip():
                    members = [ctx.guild.get_member(i) for i in parse_id_list(ids_raw)]
                    members = [m for m in members if m]
                else:
                    members = [m for m in ctx.guild.members if not m.bot and m.voice]
                result = await members.mass_move_to_voice(ctx, members, channel)
                render_result(result)
            elif choice == "7":
                ids_raw = ask("Member IDs (blank=all non-bots in voice)", default="")
                if ids_raw.strip():
                    members = [ctx.guild.get_member(i) for i in parse_id_list(ids_raw)]
                    members = [m for m in members if m]
                else:
                    members = [m for m in ctx.guild.members if not m.bot and m.voice]
                mute_raw = ask("Mute? (true/false/blank)", default="")
                deafen_raw = ask("Deafen? (true/false/blank)", default="")
                mute = None if mute_raw == "" else mute_raw.lower() == "true"
                deafen = None if deafen_raw == "" else deafen_raw.lower() == "true"
                result = await members.mass_voice_state(ctx, members, mute=mute, deafen=deafen)
                render_result(result)
            elif choice == "8":
                ids_raw = ask("Member IDs (blank=all non-bots)", default="")
                if ids_raw.strip():
                    members = [ctx.guild.get_member(i) for i in parse_id_list(ids_raw)]
                    members = [m for m in members if m]
                else:
                    members = [m for m in ctx.guild.members if not m.bot]
                content = ask("Message content")
                count = int(ask("Times per member", default="1"))
                result = await members.mass_dm(ctx, members, content, count=count)
                render_result(result)
            elif choice == "9":
                include_bots = confirm("Include bots?", default=False)
                ids = await members.scrape_members(ctx, include_bots=include_bots)
                Path("member_ids.txt").write_text("\n".join(map(str, ids)), encoding="utf-8")
                success(f"Scraped {len(ids)} member IDs to member_ids.txt")
            elif choice == "10":
                days = int(ask("Inactive days", default="30"))
                result = await members.prune_members(ctx, days=days)
                render_result(result)
            elif choice == "11":
                code = ask("Invite code or URL")
                result = await members.join_invite(ctx, code)
                render_result(result)
            elif choice == "12":
                if not await _confirm_action(ctx, "leave_guild", 1):
                    continue
                result = await members.leave_guild(ctx)
                render_result(result)
            elif choice == "13":
                await _mass_ids_menu(ctx)
        except Exception as exc:  # noqa: BLE001
            error(str(exc))


async def _messages_menu(ctx: Context) -> None:
    while True:
        menu("Messages", [
            ("1", "Purge channel"),
            ("2", "Spam messages"),
            ("3", "Webhook spam"),
            ("4", "Pin spam"),
            ("5", "React spam"),
            ("6", "Edit own messages"),
            ("7", "Delete own messages"),
            ("0", "Back"),
        ])
        choice = ask("Select", default="0")
        if choice == "0":
            return
        try:
            if choice == "1":
                cid = int(ask("Channel ID"))
                channel = ctx.guild.get_channel(cid)
                limit = int(ask("Limit", default="1000"))
                result = await messages.purge_channel(ctx, channel, limit=limit)
                render_result(result)
            elif choice == "2":
                cid = int(ask("Channel ID"))
                channel = ctx.guild.get_channel(cid)
                content = ask("Content")
                count = int(ask("Count", default="10"))
                delay = float(ask("Delay seconds", default="0.5"))
                result = await messages.spam_messages(ctx, channel, content, count, delay=delay)
                render_result(result)
            elif choice == "3":
                wid = int(ask("Webhook ID"))
                webhooks_list = await webhooks.list_webhooks(ctx)
                webhook = next((w for w in webhooks_list if w.id == wid), None)
                if webhook is None:
                    # fetch by URL fallback
                    webhook = None
                content = ask("Content")
                count = int(ask("Count", default="10"))
                delay = float(ask("Delay seconds", default="0.5"))
                if webhook is None:
                    error("Webhook not found")
                    continue
                result = await messages.webhook_spam(ctx, webhook, content, count, delay=delay)
                render_result(result)
            elif choice == "4":
                cid = int(ask("Channel ID"))
                channel = ctx.guild.get_channel(cid)
                count = int(ask("Count", default="10"))
                result = await messages.pin_spam(ctx, channel, count=count)
                render_result(result)
            elif choice == "5":
                cid = int(ask("Channel ID"))
                channel = ctx.guild.get_channel(cid)
                emoji = ask("Emoji", default="🔥")
                count = int(ask("Count", default="10"))
                result = await messages.react_spam(ctx, channel, emoji, count=count)
                render_result(result)
            elif choice == "6":
                cid = int(ask("Channel ID"))
                channel = ctx.guild.get_channel(cid)
                content = ask("New content")
                limit = int(ask("Limit", default="50"))
                result = await messages.edit_own_messages(ctx, channel, content, limit=limit)
                render_result(result)
            elif choice == "7":
                cid = int(ask("Channel ID"))
                channel = ctx.guild.get_channel(cid)
                limit = int(ask("Limit", default="1000"))
                result = await messages.delete_own_messages(ctx, channel, limit=limit)
                render_result(result)
        except Exception as exc:  # noqa: BLE001
            error(str(exc))


async def _server_menu(ctx: Context) -> None:
    while True:
        menu("Server", [
            ("1", "Rename server"),
            ("2", "Set icon"),
            ("3", "Set banner"),
            ("4", "Verification level"),
            ("5", "Notifications"),
            ("6", "Content filter"),
            ("7", "System channel"),
            ("8", "AFK"),
            ("0", "Back"),
        ])
        choice = ask("Select", default="0")
        if choice == "0":
            return
        try:
            if choice == "1":
                name = ask("New server name")
                result = await server.rename_server(ctx, name)
                render_result(result)
            elif choice == "2":
                path = ask("Icon path or URL")
                result = await server.set_icon(ctx, path)
                render_result(result)
            elif choice == "3":
                path = ask("Banner path or URL")
                result = await server.set_banner(ctx, path)
                render_result(result)
            elif choice == "4":
                level = ask("Verification level (none/low/medium/high/very_high)", default="none")
                mapping = {
                    "none": None,
                }
                # Use discord enum via string fallback not exact; attempt attribute
                import discord

                value = getattr(discord.VerificationLevel, level, None)
                result = await server.set_verification_level(ctx, value)
                render_result(result)
            elif choice == "5":
                level = ask("Notification level (all_messages/only_mentions)", default="only_mentions")
                import discord

                value = getattr(discord.NotificationLevel, level, None)
                result = await server.set_notifications(ctx, value)
                render_result(result)
            elif choice == "6":
                level = ask("Content filter (disabled/members_without_roles/all_members)", default="disabled")
                import discord

                value = getattr(discord.ContentFilter, level, None)
                result = await server.set_content_filter(ctx, value)
                render_result(result)
            elif choice == "7":
                cid = int(ask("Channel ID"))
                channel = ctx.guild.get_channel(cid)
                result = await server.set_system_channel(ctx, channel)
                render_result(result)
            elif choice == "8":
                cid = int(ask("AFK channel ID"))
                channel = ctx.guild.get_channel(cid) if cid else None
                timeout = int(ask("AFK timeout seconds", default="300"))
                result = await server.set_afk(ctx, channel, timeout)
                render_result(result)
        except Exception as exc:  # noqa: BLE001
            error(str(exc))


async def _webhooks_menu(ctx: Context) -> None:
    while True:
        menu("Webhooks", [
            ("1", "List webhooks"),
            ("2", "Create webhooks"),
            ("3", "Delete webhooks"),
            ("4", "Webhook spam"),
            ("0", "Back"),
        ])
        choice = ask("Select", default="0")
        if choice == "0":
            return
        try:
            if choice == "1":
                whs = await webhooks.list_webhooks(ctx)
                for w in whs:
                    console.print(f"{w.id} | {w.name} | {getattr(w, 'channel_id', '')}")
            elif choice == "2":
                cid = int(ask("Channel ID"))
                channel = ctx.guild.get_channel(cid)
                names = parse_str_list(ask("Webhook names comma", default="webhook"))
                # expand count
                count = int(ask("Count", default="1"))
                names = names * count if len(names) == 1 else names
                result = await webhooks.create_webhooks(ctx, channel, names)
                render_result(result)
            elif choice == "3":
                ids = parse_id_list(ask("Webhook IDs comma"))
                whs = await webhooks.list_webhooks(ctx)
                selected = [w for w in whs if w.id in ids]
                if not await _confirm_action(ctx, "delete_webhooks", len(selected)):
                    continue
                result = await webhooks.delete_webhooks(ctx, selected)
                render_result(result)
            elif choice == "4":
                wid = int(ask("Webhook ID"))
                whs = await webhooks.list_webhooks(ctx)
                webhook = next((w for w in whs if w.id == wid), None)
                if webhook is None:
                    error("Webhook not found")
                    continue
                content = ask("Content")
                count = int(ask("Count", default="10"))
                delay = float(ask("Delay seconds", default="0.5"))
                result = await messages.webhook_spam(ctx, webhook, content, count, delay=delay)
                render_result(result)
        except Exception as exc:  # noqa: BLE001
            error(str(exc))


async def _emojis_menu(ctx: Context) -> None:
    while True:
        menu("Emojis/Stickers", [
            ("1", "Delete emojis"),
            ("2", "Create emoji"),
            ("3", "Rename emoji"),
            ("4", "Delete stickers"),
            ("5", "Create sticker"),
            ("0", "Back"),
        ])
        choice = ask("Select", default="0")
        if choice == "0":
            return
        try:
            if choice == "1":
                emojis_list = list(ctx.guild.emojis)
                ids = parse_id_list(ask("Emoji IDs comma (blank=all)", default=""))
                selected = [e for e in emojis_list if not ids or e.id in ids]
                if not await _confirm_action(ctx, "delete_emojis", len(selected)):
                    continue
                result = await emojis.delete_emojis(ctx, selected)
                render_result(result)
            elif choice == "2":
                name = ask("Emoji name")
                path = ask("Image path or URL")
                result = await emojis.create_emoji(ctx, name, path)
                render_result(result)
            elif choice == "3":
                eid = int(ask("Emoji ID"))
                emoji = next((e for e in ctx.guild.emojis if e.id == eid), None)
                name = ask("New name")
                result = await emojis.rename_emoji(ctx, emoji, name)
                render_result(result)
            elif choice == "4":
                stickers = list(ctx.guild.stickers)
                ids = parse_id_list(ask("Sticker IDs comma (blank=all)", default=""))
                selected = [s for s in stickers if not ids or s.id in ids]
                if not await _confirm_action(ctx, "delete_stickers", len(selected)):
                    continue
                result = await emojis.delete_stickers(ctx, selected)
                render_result(result)
            elif choice == "5":
                name = ask("Sticker name")
                path = ask("Image path")
                desc = ask("Description", default="")
                result = await emojis.create_sticker(ctx, name, path, desc)
                render_result(result)
        except Exception as exc:  # noqa: BLE001
            error(str(exc))


async def _threads_menu(ctx: Context) -> None:
    while True:
        menu("Threads", [
            ("1", "Create threads"),
            ("2", "Archive all threads"),
            ("3", "Delete all threads"),
            ("0", "Back"),
        ])
        choice = ask("Select", default="0")
        if choice == "0":
            return
        try:
            if choice == "1":
                cid = int(ask("Channel ID"))
                channel = ctx.guild.get_channel(cid)
                template = ask("Thread name template", default="thread-{i}")
                count = int(ask("Count", default="10"))
                result = await threads.create_threads(ctx, channel, template, count)
                render_result(result)
            elif choice == "2":
                all_threads = list(ctx.guild.threads)
                result = await threads.archive_threads(ctx, all_threads)
                render_result(result)
            elif choice == "3":
                all_threads = list(ctx.guild.threads)
                if not await _confirm_action(ctx, "delete_threads", len(all_threads)):
                    continue
                result = await threads.delete_threads(ctx, all_threads)
                render_result(result)
        except Exception as exc:  # noqa: BLE001
            error(str(exc))


async def _integrations_menu(ctx: Context) -> None:
    while True:
        menu("Integrations", [
            ("1", "List bots"),
            ("2", "Remove bots"),
            ("0", "Back"),
        ])
        choice = ask("Select", default="0")
        if choice == "0":
            return
        try:
            if choice == "1":
                bots = await integrations.list_bots(ctx)
                for b in bots:
                    console.print(f"{b.id} | {b}")
            elif choice == "2":
                bots = await integrations.list_bots(ctx)
                if not await _confirm_action(ctx, "remove_bots", len(bots)):
                    continue
                result = await integrations.remove_bots(ctx, bots)
                render_result(result)
        except Exception as exc:  # noqa: BLE001
            error(str(exc))


async def _raid_menu(ctx: Context) -> None:
    while True:
        menu("Raid/Utility", [
            ("1", "Token check"),
            ("2", "Guild scrape"),
            ("3", "Permission audit"),
            ("4", "Backup guild"),
            ("5", "Restore guild"),
            ("6", "Leave all guilds"),
            ("7", "Full server nuke (all-in-one)"),
            ("0", "Back"),
        ])
        choice = ask("Select", default="0")
        if choice == "0":
            return
        try:
            if choice == "1":
                info(str(await raid.token_check(ctx.client)))
            elif choice == "2":
                info(str(await raid.guild_scrape(ctx)))
            elif choice == "3":
                info(str(await raid.permission_audit(ctx)))
            elif choice == "4":
                result = await utility.backup_guild(ctx)
                render_result(result)
                if result.details.get("path"):
                    success(f"Backup: {result.details['path']}")
            elif choice == "5":
                path = ask("Backup path")
                result = await utility.restore_guild(ctx, path)
                render_result(result)
            elif choice == "6":
                if not await _confirm_action(ctx, "leave_all_guilds", len(ctx.client.guilds)):
                    continue
                result = await raid.leave_all_guilds(ctx)
                render_result(result)
            elif choice == "7":
                warning("FULL SERVER NUKE: this destroys the entire guild.")
                if not await _confirm_action(ctx, "full_server_nuke", 1):
                    continue
                extra = ask("Type NUKE to execute full nuke")
                if extra.strip() != "NUKE":
                    warning("Cancelled")
                    continue
                spam_channels = int(ask("Spam channels", default="25"))
                spam_messages = int(ask("Spam messages per channel", default="10"))
                results = await nuke_all.full_nuke(ctx, spam_channels=spam_channels, spam_messages=spam_messages)
                for res in results:
                    render_result(res)
        except Exception as exc:  # noqa: BLE001
            error(str(exc))


async def _switch_account(ctx, config):
    await close_client(ctx.client)
    client, mode = await _login(config)
    ctx.client = client
    ctx.mode = mode
    ctx.rate_limiter = RateLimiter(max_concurrency=config.max_workers_for_mode(mode))
    success(f"Switched account: {client.describe()}")


async def _settings_menu(ctx):
    while True:
        profiles = list_profiles(ctx.mode)
        menu("Settings", [
            ("1", f"Toggle dry-run (current={ctx.dry_run.enabled})"),
            ("2", "Set concurrency"),
            ("3", "Save token to profile"),
            ("4", "Load/switch profile"),
            ("5", "Delete profile"),
            ("6", "Switch account/token manually"),
            ("0", "Back"),
        ])
        choice = ask("Select", default="0")
        if choice == "0":
            return
        try:
            if choice == "1":
                ctx.dry_run.enabled = not ctx.dry_run.enabled
                success(f"dry_run={ctx.dry_run.enabled}")
            elif choice == "2":
                value = int(ask("Max concurrency", default=str(ctx.rate_limiter.max_concurrency)))
                ctx.rate_limiter.max_concurrency = max(1, value)
                ctx.rate_limiter._semaphore = asyncio.Semaphore(ctx.rate_limiter.max_concurrency)
                success(f"max_concurrency={ctx.rate_limiter.max_concurrency}")
            elif choice == "3":
                profile = ask("Profile name", default="default")
                token = ask("Token")
                if save_profile(ctx.mode, profile, token):
                    success(f"Token saved to profile '{profile}'")
                else:
                    warning("Could not save token (keyring unavailable)")
            elif choice == "4":
                if not profiles:
                    warning("No saved profiles")
                    continue
                console.print("Profiles: " + ", ".join(profiles))
                profile = ask("Profile name", default=profiles[0])
                token = get_token(ctx.mode, profile)
                if not token:
                    warning("Profile has no token")
                    continue
                await close_client(ctx.client)
                client = await create_client(ctx.mode, token, make_intents(ctx.mode), proxy=getattr(ctx.config, "proxy", None))
                mode = client.mode
                ctx.client = client
                ctx.mode = mode
                ctx.rate_limiter = RateLimiter(max_concurrency=ctx.config.max_workers_for_mode(mode))
                success(f"Loaded profile '{profile}'")
            elif choice == "5":
                if not profiles:
                    warning("No saved profiles")
                    continue
                console.print("Profiles: " + ", ".join(profiles))
                profile = ask("Profile name", default=profiles[0])
                if delete_profile(ctx.mode, profile):
                    success(f"Deleted profile '{profile}'")
                else:
                    warning("Profile/token deletion failed or keyring unavailable")
            elif choice == "6":
                await _switch_account(ctx, ctx.config)
                raise AccountSwitched()
        except AccountSwitched:
            raise
        except Exception as exc:
            error(str(exc))


async def _advanced_menu(ctx):
    while True:
        menu("Advanced", [
            ("1", "Channel permission nuke"),
            ("2", "Role permission nuke all"),
            ("3", "Spam all channels"),
            ("4", "Chaos rename all"),
            ("5", "Purge all channels"),
            ("6", "Mass timeout all"),
            ("0", "Back"),
        ])
        choice = ask("Select", default="0")
        if choice == "0":
            return
        try:
            if choice == "1":
                ids = await _channel_ids_prompt(ctx.guild)
                chans = _channels_by_ids(ctx.guild, ids)
                allow = confirm("Allow instead of deny?", default=False)
                if not await _confirm_action(ctx, "channel_permission_nuke", len(chans)):
                    continue
                result = await advanced.channel_permission_nuke(ctx, chans, allow)
                render_result(result)
            elif choice == "2":
                ids = await _role_ids_prompt(ctx.guild)
                roles_list = _roles_by_ids(ctx.guild, ids)
                admin = confirm("Grant administrator?", default=True)
                if not await _confirm_action(ctx, "role_permission_nuke_all", len(roles_list)):
                    continue
                result = await advanced.role_permission_nuke_all(ctx, roles_list, administrator=admin)
                render_result(result)
            elif choice == "3":
                content = ask("Content", default="DARK NUKER")
                count = int(ask("Count per channel", default="5"))
                delay = float(ask("Delay seconds", default="0.2"))
                result = await advanced.spam_all_channels(ctx, content, count, delay=delay)
                render_result(result)
            elif choice == "4":
                if not await _confirm_action(ctx, "chaos_rename", len(ctx.guild.channels) + len(ctx.guild.roles)):
                    continue
                result = await advanced.chaos_rename(ctx)
                render_result(result)
            elif choice == "5":
                limit = int(ask("Limit per channel", default="1000"))
                if not await _confirm_action(ctx, "purge_all_channels", len(ctx.guild.text_channels)):
                    continue
                result = await advanced.purge_all_channels(ctx, limit=limit)
                render_result(result)
            elif choice == "6":
                seconds = int(ask("Timeout seconds", default="3600"))
                if not await _confirm_action(ctx, "mass_timeout_all", len([m for m in ctx.guild.members if not m.bot])):
                    continue
                result = await advanced.mass_timeout_all(ctx, seconds)
                render_result(result)
        except Exception as exc:
            error(str(exc))

async def _mass_ids_menu(ctx):
    while True:
        menu('Mass ID Operations', [
            ('1','Mass ban IDs'),
            ('2','Mass kick IDs'),
            ('3','Mass timeout IDs'),
            ('4','Mass unban IDs'),
            ('5','Save ID list to file'),
            ('0','Back'),
        ])
        choice = ask('Select', default='0')
        if choice == '0':
            return
        try:
            if choice == '1':
                ids = parse_id_list(ask('User IDs comma'))
                mems = [ctx.guild.get_member(i) for i in ids]
                mems = [m for m in mems if m]
                if not await _confirm_action(ctx, 'mass_ban', len(mems)):
                    continue
                result = await members.mass_ban(ctx, mems, reason=ask('Reason', default='Nuked'), delete_message_days=int(ask('Delete message days 0-7', default='0')))
                render_result(result)
            elif choice == '2':
                ids = parse_id_list(ask('User IDs comma'))
                mems = [ctx.guild.get_member(i) for i in ids]
                mems = [m for m in mems if m]
                if not await _confirm_action(ctx, 'mass_kick', len(mems)):
                    continue
                result = await members.mass_kick(ctx, mems, reason=ask('Reason', default='Nuked'))
                render_result(result)
            elif choice == '3':
                ids = parse_id_list(ask('User IDs comma'))
                mems = [ctx.guild.get_member(i) for i in ids]
                mems = [m for m in mems if m]
                result = await members.mass_timeout(ctx, mems, int(ask('Timeout seconds', default='3600')))
                render_result(result)
            elif choice == '4':
                ids = parse_id_list(ask('User IDs comma'))
                result = await members.mass_unban(ctx, ids)
                render_result(result)
            elif choice == '5':
                ids = parse_id_list(ask('User IDs comma'))
                from pathlib import Path as _P
                _P('id_list.txt').write_text('\n'.join(map(str, ids)), encoding='utf-8')
                success(f'Saved {len(ids)} IDs to id_list.txt')
        except Exception as exc:
            error(str(exc))
