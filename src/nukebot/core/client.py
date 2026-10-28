"""Discord client wrapper for bot and selfbot modes."""

from __future__ import annotations

import asyncio
from typing import Any

import discord

from nukebot.storage.logging import get_logger

log = get_logger("client")


class NukeClient(discord.Client):
    def __init__(self, mode: str, intents: discord.Intents | None = None, proxy: str | None = None, **kwargs: Any):
        self.mode = mode
        self.is_bot_mode = mode == "bot"
        if proxy:
            kwargs["proxy"] = proxy
        super().__init__(intents=intents or discord.Intents.all(), **kwargs)

    async def login(self, token: str, *, bot: bool | None = None, **kwargs: Any) -> None:
        # discord.py-self detects bot/user tokens automatically.
        await super().login(token, **kwargs)

    async def start(self, token: str, *, reconnect: bool = True, **kwargs: Any) -> None:
        await super().start(token, reconnect=reconnect, **kwargs)

    def describe(self) -> str:
        user = self.user
        if user is None:
            return f"mode={self.mode} (not connected)"
        return f"mode={self.mode} user={user} id={user.id}"


async def create_client(mode: str, token: str, intents: discord.Intents | None = None, proxy: str | None = None) -> NukeClient:
    client = NukeClient(mode=mode, intents=intents, proxy=proxy)
    await client.login(token)
    if client.user is not None:
        client.is_bot_mode = bool(getattr(client.user, "bot", False))
        client.mode = "bot" if client.is_bot_mode else "selfbot"
    client._connect_task = asyncio.create_task(client.connect(reconnect=True))
    try:
        await asyncio.wait_for(client.wait_until_ready(), timeout=30)
    except asyncio.TimeoutError as exc:
        raise RuntimeError("Timed out waiting for Discord connection") from exc
    log.info("Logged in: %s", client.describe())
    return client


async def close_client(client: NukeClient) -> None:
    task = getattr(client, "_connect_task", None)
    if task is not None and not task.done():
        task.cancel()
        try:
            await task
        except (asyncio.CancelledError, Exception):  # noqa: BLE001
            pass
    if not client.is_closed():
        await client.close()
