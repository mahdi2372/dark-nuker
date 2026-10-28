"""Role nuke and management features."""

from __future__ import annotations

import random

import discord

from nukebot.core.rate_limit import RateLimiter
from nukebot.core.templates import render_template
from nukebot.features.common import Context, Result


async def create_roles(
    ctx: Context,
    name_template: str,
    count: int,
    color: int | None = None,
    hoist: bool = False,
    mentionable: bool = False,
    administrator: bool = False,
) -> Result:
    result = Result(action="create_roles")
    if ctx.dry_run.enabled:
        ctx.dry_run.record("create_role", "role", count)
        result.success = count
        return result
    permissions = discord.Permissions.all() if administrator else discord.Permissions.none()
    for i in range(1, count + 1):
        name = render_template(name_template, i, {"guild": ctx.guild.name})
        role_color = discord.Color(color if color is not None else random.randint(0, 0xFFFFFF))
        try:
            await ctx.rate_limiter.run(
                lambda name=name, role_color=role_color: ctx.guild.create_role(
                    name=name,
                    color=role_color,
                    hoist=hoist,
                    mentionable=mentionable,
                    permissions=permissions,
                ),
                "create_role",
            )
            result.success += 1
        except Exception as exc:  # noqa: BLE001
            result.add_error(f"create {name}: {exc}")
    return result


async def delete_roles(ctx: Context, roles: list[discord.Role]) -> Result:
    result = Result(action="delete_roles")
    if ctx.dry_run.enabled:
        ctx.dry_run.record("delete_role", "role", len(roles))
        result.success = len(roles)
        return result
    for role in roles:
        try:
            await ctx.rate_limiter.run(lambda role=role: role.delete(), "delete_role")
            result.success += 1
        except Exception as exc:  # noqa: BLE001
            result.add_error(f"delete {role.name}: {exc}")
    return result


async def rename_roles(ctx: Context, roles: list[discord.Role], template: str) -> Result:
    result = Result(action="rename_roles")
    if ctx.dry_run.enabled:
        ctx.dry_run.record("rename_role", "role", len(roles))
        result.success = len(roles)
        return result
    for index, role in enumerate(roles, start=1):
        name = render_template(template, index, {"name": role.name, "guild": ctx.guild.name})
        try:
            await ctx.rate_limiter.run(lambda role=role, name=name: role.edit(name=name), "rename_role")
            result.success += 1
        except Exception as exc:  # noqa: BLE001
            result.add_error(f"rename {role.id}: {exc}")
    return result


async def mass_assign_role(ctx: Context, role: discord.Role, members: list[Any], remove: bool = False) -> Result:
    result = Result(action="remove_role" if remove else "assign_role")
    if ctx.dry_run.enabled:
        ctx.dry_run.record("mass_role", role.name, len(members))
        result.success = len(members)
        return result
    for member in members:
        try:
            if remove:
                await ctx.rate_limiter.run(lambda member=member, role=role: member.remove_roles(role), "remove_role")
            else:
                await ctx.rate_limiter.run(lambda member=member, role=role: member.add_roles(role), "add_role")
            result.success += 1
        except Exception as exc:  # noqa: BLE001
            result.add_error(f"role {role.id} member {getattr(member, 'id', member)}: {exc}")
    return result


async def permission_nuke(ctx: Context, role: discord.Role | None = None) -> Result:
    result = Result(action="permission_nuke")
    target = role or ctx.guild.default_role
    if ctx.dry_run.enabled:
        ctx.dry_run.record("permission_nuke", target.name, 1)
        result.success = 1
        return result
    try:
        await ctx.rate_limiter.run(
            lambda: target.edit(permissions=discord.Permissions.all()),
            "permission_nuke",
        )
        result.success = 1
    except Exception as exc:  # noqa: BLE001
        result.add_error(f"permission_nuke {target.id}: {exc}")
    return result


async def role_color_cycle(ctx: Context, role: discord.Role, colors: list[int], delay: float = 1.0) -> Result:
    result = Result(action="role_color_cycle")
    if ctx.dry_run.enabled:
        ctx.dry_run.record("role_color_cycle", role.name, len(colors))
        result.success = len(colors)
        return result
    for color in colors:
        try:
            await ctx.rate_limiter.run(lambda color=color: role.edit(color=discord.Color(color)), "role_color")
            await asyncio_sleep(delay)
            result.success += 1
        except Exception as exc: # noqa: BLE001
            result.add_error(f"color {role.id}: {exc}")
    return result


async def asyncio_sleep(seconds: float) -> None:
    import asyncio

    await asyncio.sleep(seconds)


async def hoist_toggle(ctx: Context, roles: list[discord.Role], hoist: bool) -> Result:
    result = Result(action="hoist_toggle")
    if ctx.dry_run.enabled:
        ctx.dry_run.record("hoist_toggle", "role", len(roles))
        result.success = len(roles)
        return result
    for role in roles:
        try:
            await ctx.rate_limiter.run(lambda role=role: role.edit(hoist=hoist), "hoist_toggle")
            result.success += 1
        except Exception as exc:  # noqa: BLE001
            result.add_error(f"hoist {role.id}: {exc}")
    return result


async def reorder_roles(ctx: Context, roles: list[discord.Role]) -> Result:
    result = Result(action="reorder_roles")
    if ctx.dry_run.enabled:
        ctx.dry_run.record("reorder_roles", "role", len(roles))
        result.success = len(roles)
        return result
    try:
        await ctx.rate_limiter.run(lambda: ctx.guild.edit_role_positions(positions={r: i for i, r in enumerate(roles)}), "reorder_roles")
        result.success = len(roles)
    except Exception as exc:  # noqa: BLE001
        result.add_error(f"reorder: {exc}")
    return result
