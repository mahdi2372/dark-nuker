"""Utility features."""

from __future__ import annotations

from nukebot.backup.backup import create_backup
from nukebot.backup.restore import restore_backup
from nukebot.features.common import Context, Result


async def backup_guild(ctx: Context) -> Result:
    result = Result(action="backup_guild")
    if ctx.dry_run.enabled:
        ctx.dry_run.record("backup_guild", ctx.guild.name, 1)
        result.success = 1
        return result
    try:
        path = await create_backup(ctx.guild, ctx.config.backup_dir if hasattr(ctx, "config") else "backups")
        result.details["path"] = str(path)
        result.success = 1
    except Exception as exc:  # noqa: BLE001
        result.add_error(f"backup: {exc}")
    return result


async def restore_guild(ctx: Context, backup_path: str) -> Result:
    result = Result(action="restore_guild")
    if ctx.dry_run.enabled:
        ctx.dry_run.record("restore_guild", backup_path, 1)
        result.success = 1
        return result
    try:
        stats = await restore_backup(ctx.guild, backup_path, ctx.rate_limiter)
        result.details.update(stats)
        result.success = stats.get("roles", 0) + stats.get("channels", 0) + stats.get("webhooks", 0)
        result.failed = stats.get("failures", 0)
    except Exception as exc:  # noqa: BLE001
        result.add_error(f"restore: {exc}")
    return result


async def guild_info(ctx: Context) -> dict[str, object]:
    guild = ctx.guild
    return {
        "id": guild.id,
        "name": guild.name,
        "owner_id": guild.owner_id,
        "member_count": guild.member_count,
        "channel_count": len(guild.channels),
        "role_count": len(guild.roles),
        "emoji_count": len(guild.emojis),
        "sticker_count": len(guild.stickers),
        "created_at": guild.created_at.isoformat() if guild.created_at else None,
        "verification_level": str(guild.verification_level),
        "premium_tier": guild.premium_tier,
        "description": guild.description,
    }
