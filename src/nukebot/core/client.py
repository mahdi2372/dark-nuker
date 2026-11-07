"""Discord client wrapper for bot and selfbot modes."""

from __future__ import annotations

import asyncio

import discord

from nukebot.storage.logging import get_logger

log = get_logger("client")

_BOT_INTENTS = 32767


class NukeClient(discord.Client):
    def __init__(self, mode: str, proxy: str | None = None, **kwargs: Any):
        self.mode = mode
        self.is_bot_mode = mode == "bot"
        if proxy:
            kwargs["proxy"] = proxy
        super().__init__(**kwargs)

    async def login(self, token: str, *, bot: bool | None = None, **kwargs: Any) -> None:
        # discord.py-self detects bot/user tokens automatically when prefixed.
        await super().login(token, **kwargs)

    async def start(self, token: str, *, reconnect: bool = True, **kwargs: Any) -> None:
        await super().start(token, reconnect=reconnect, **kwargs)

    def describe(self) -> str:
        user = self.user
        if user is None:
            return f"mode={self.mode} (not connected)"
        return f"mode={self.mode} user={user} id={user.id}"


async def _patched_identify(self) -> None:
    presence = {
        "status": "unknown",
        "since": self.idle_since,
        "activities": [],
        "afk": self.afk,
    }
    existing = self._connection.current_session
    if existing is not None:
        presence["status"] = str(existing.status) if existing.status is not None and str(existing.status) != "offline" else "invisible"
        presence["activities"] = [a.to_dict() for a in existing.activities]

    properties = self._headers.gateway_properties

    payload = {
        "op": self.IDENTIFY,
        "d": {
            "token": self.token,
            "capabilities": self.capabilities.value,
            "properties": properties,
            "presence": presence,
            "compress": not self._transport_compression,
            "client_state": {"guild_versions": {}},
            "intents": _BOT_INTENTS,
        },
    }

    await self.call_hooks("before_identify", initial=self._initial_identify)
    await self.send_as_json(payload)
    self._initial_identify = True


def enable_bot_intents(intents: int) -> None:
    global _BOT_INTENTS
    _BOT_INTENTS = intents
    import discord.gateway

    discord.gateway.DiscordWebSocket.identify = _patched_identify


async def create_client(mode: str, token: str, proxy: str | None = None) -> NukeClient:
    token = token.strip()

    # Try as a user token first.
    try:
        client = NukeClient(mode=mode, proxy=proxy)
        await client.login(token)
        if client.user is not None and not getattr(client.user, "bot", False):
            client.is_bot_mode = False
            client.mode = "selfbot"
            client._connect_task = asyncio.create_task(client.connect(reconnect=True))
            await asyncio.wait_for(client.wait_until_ready(), timeout=30)
            log.info("Logged in: %s", client.describe())
            return client
        await close_client(client)
    except Exception:  # noqa: BLE001
        pass

    last_error = None
    for intents_mask in (32767, 14336, 513, 1):
        try:
            enable_bot_intents(intents_mask)
            client = NukeClient(mode="bot", proxy=proxy)
            await client.login(f"Bot {token}")
            if client.user is None or not getattr(client.user, "bot", False):
                await close_client(client)
                continue
            client.is_bot_mode = True
            client.mode = "bot"
            client._connect_task = asyncio.create_task(client.connect(reconnect=True))
            await asyncio.wait_for(client.wait_until_ready(), timeout=30)
            log.info("Logged in: %s", client.describe())
            return client
        except Exception as exc:  # noqa: BLE001
            last_error = exc
            try:
                await close_client(client)
            except Exception:  # noqa: BLE001
                pass
    if last_error is not None:
        raise last_error
    raise RuntimeError("Unable to log in with the provided token")


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
    await asyncio.sleep(0)
