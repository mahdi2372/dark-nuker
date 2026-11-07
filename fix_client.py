from pathlib import Path

p = Path(r"C:\Users\mahdi\Desktop\discord nuke bot\src\nukebot\core\client.py")
s = p.read_text(encoding="utf-8")

old = '''async def create_client(mode: str, token: str, intents=None, proxy: str | None = None) -> NukeClient:
    client = NukeClient(mode=mode, proxy=proxy)
    await client.login(token)
    if client.user is not None:
        client.is_bot_mode = bool(getattr(client.user, "bot", False))
        client.mode = "bot" if client.is_bot_mode else "selfbot"
    client._connection.http.token = None
    client._connect_task = asyncio.create_task(client.connect(reconnect=True))
    try:
        await asyncio.wait_for(client.wait_until_ready(), timeout=30)
    except asyncio.TimeoutError as exc:
        raise RuntimeError("Timed out waiting for Discord connection") from exc
    log.info("Logged in: %s", client.describe())
    return client
'''

# The actual current block may differ; do a simpler replacement by locating the function.
import re
pattern = re.compile(r"async def create_client\(.*?\n    return client\n", re.S)
new = '''async def create_client(mode: str, token: str, proxy: str | None = None) -> NukeClient:
    client = NukeClient(mode=mode, proxy=proxy)
    token = token.strip()
    last_error = None
    for candidate in (token, f"Bot {token}"):
        try:
            await client.login(candidate)
            break
        except Exception as exc:  # noqa: BLE001
            last_error = exc
            client._connection.http.token = None
    else:
        raise last_error
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
'''
s2 = pattern.sub(new, s, count=1)
assert s2 != s, "No replacement made"
p.write_text(s2, encoding="utf-8")
print("ok")
