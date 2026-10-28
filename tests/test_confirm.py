import pytest

from nukebot.core.confirm import confirm_destructive


@pytest.mark.asyncio
async def test_confirm_destructive_success():
    answers = iter(["MyGuild", "CONFIRM"])

    async def inp(prompt):
        return next(answers)

    outputs = []

    def out(msg):
        outputs.append(msg)

    result = await confirm_destructive(inp, out, "MyGuild", "delete", 5, "channels")
    assert result.approved is True


@pytest.mark.asyncio
async def test_confirm_destructive_wrong_name():
    answers = iter(["Wrong", "CONFIRM"])

    async def inp(prompt):
        return next(answers)

    result = await confirm_destructive(inp, lambda m: None, "MyGuild", "delete", 5, "channels")
    assert result.approved is False
    assert "mismatch" in result.reason
