from pathlib import Path
import re

p = Path(r"C:\Users\mahdi\Desktop\discord nuke bot\src\nukebot\core\client.py")
s = p.read_text(encoding="utf-8")

# Replace create_client function
pattern = re.compile(r"async def create_client\(.*?\n    log\.info\(\"Logged in: %s\", client\.describe\(\)\)\n    return client\n", re.S)
new_func = '''async def create_client(mode: str, token: str, proxy: str | None = None) -> NukeClient:
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

    # Bot token: prefix with "Bot " and patch gateway intents.
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
'''
s2 = pattern.sub(new_func, s, count=1)
assert s2 != s, "create_client not replaced"
p.write_text(s2, encoding="utf-8")
print("ok")
'''
p2 = Path(r"C:\Users\mahdi\Desktop\discord nuke bot\fix_client2.py")
p2.write_text(s2 if False else open(str(p)).read(), encoding="utf-8")
print("done")
'''
# Actually just write file directly:
p.write_text(s2, encoding="utf-8")
print("written")
