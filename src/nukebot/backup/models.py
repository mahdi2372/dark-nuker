"""Backup data models."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class ChannelBackup:
    id: int
    name: str
    type: str
    position: int
    category_id: int | None = None
    topic: str | None = None
    nsfw: bool = False
    slowmode_delay: int = 0
    bitrate: int | None = None
    user_limit: int | None = None
    overwrites: list[dict[str, Any]] = field(default_factory=list)


@dataclass
class RoleBackup:
    id: int
    name: str
    color: int
    hoist: bool
    mentionable: bool
    permissions: int
    position: int


@dataclass
class GuildBackup:
    version: int = 1
    guild_id: int = 0
    guild_name: str = ""
    created_at: str = ""
    channels: list[dict[str, Any]] = field(default_factory=list)
    roles: list[dict[str, Any]] = field(default_factory=list)
    emojis: list[dict[str, Any]] = field(default_factory=list)
    stickers: list[dict[str, Any]] = field(default_factory=list)
    webhooks: list[dict[str, Any]] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
