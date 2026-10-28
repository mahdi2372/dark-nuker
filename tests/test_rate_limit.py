import asyncio
import pytest

from nukebot.core.rate_limit import RateLimiter


@pytest.mark.asyncio
async def test_rate_limiter_runs():
    rl = RateLimiter(max_concurrency=2)
    async def work(value):
        await asyncio.sleep(0)
        return value * 2
    results = await rl.map([1, 2, 3], work, label="work")
    assert sorted(results) == [2, 4, 6]


@pytest.mark.asyncio
async def test_rate_limiter_single():
    rl = RateLimiter(max_concurrency=1)

    async def work():
        return 42

    assert await rl.run(work, "single") == 42
