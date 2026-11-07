"""Patch discord.py-self gateway identify to include bot intents."""

from __future__ import annotations

import discord.gateway

_BOT_INTENTS = 32767


def _patched_identify(self) -> None:
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

    import asyncio as _asyncio

    async def _send():
        await self.call_hooks("before_identify", initial=self._initial_identify)
        await self.send_as_json(payload)
        _log.debug("Gateway has sent the IDENTIFY payload.")
        self._initial_identify = True

    # identify is async; call hooks/send in a coroutine wrapper.
    _asyncio.get_event_loop()

# The above is not usable as async; instead define an async function.
async def patched_identify(self) -> None:
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
    discord.gateway._log.debug("Gateway has sent the IDENTIFY payload.")
    self._initial_identify = True


def enable_bot_intents(intents: int) -> None:
    global _BOT_INTENTS
    _BOT_INTENTS = intents
    discord.gateway.DiscordWebSocket.identify = patched_identify
