from pathlib import Path

p = Path(r"C:\Users\mahdi\Desktop\discord nuke bot\src\nukebot\core\client.py")
lines = p.read_text(encoding="utf-8").splitlines()
start = next(i for i, l in enumerate(lines) if l.startswith("async def create_client"))
end = next(i for i, l in enumerate(lines) if l.startswith("async def close_client"))

new = [
"async def create_client(mode: str, token: str, proxy: str | None = None) -> NukeClient:",
"    token = token.strip()",
"    # Try as a user token first.",
"    try:",
"        client = NukeClient(mode=mode, proxy=proxy)",
"        await client.login(token)",
"        if client.user is not None and not getattr(client.user, \"bot\", False):",
"            client.is_bot_mode = False",
"            client.mode = \"selfbot\"",
"            client._connect_task = asyncio.create_task(client.connect(reconnect=True))",
"            await asyncio.wait_for(client.wait_until_ready(), timeout=30)",
"            log.info(\"Logged in: %s\", client.describe())",
"            return client",
"        await close_client(client)",
"    except Exception:  # noqa: BLE001",
"        pass",
"",
"    last_error = None",
"    for intents_mask in (32767, 14336, 513, 1):",
"        try:",
"            enable_bot_intents(intents_mask)",
"            client = NukeClient(mode=\"bot\", proxy=proxy)",
"            await client.login(f\"Bot {token}\")",
"            if client.user is None or not getattr(client.user, \"bot\", False):",
"                await close_client(client)",
"                continue",
"            client.is_bot_mode = True",
"            client.mode = \"bot\"",
"            client._connect_task = asyncio.create_task(client.connect(reconnect=True))",
"            await asyncio.wait_for(client.wait_until_ready(), timeout=30)",
"            log.info(\"Logged in: %s\", client.describe())",
"            return client",
"        except Exception as exc:  # noqa: BLE001",
"            last_error = exc",
"            try:",
"                await close_client(client)",
"            except Exception:  # noqa: BLE001",
"                pass",
"    if last_error is not None:",
"        raise last_error",
"    raise RuntimeError(\"Unable to log in with the provided token\")",
"",
]

lines[start:end] = new
p.write_text("\n".join(lines) + "\n", encoding="utf-8")
print("done")
