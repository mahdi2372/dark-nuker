"""Adaptive rate limiter for Discord API calls."""

from __future__ import annotations

import asyncio
import random
from dataclasses import dataclass, field
from typing import Awaitable, Callable, TypeVar

import discord

from nukebot.storage.logging import get_logger

log = get_logger("rate_limit")

T = TypeVar("T")


@dataclass
class RateLimitStats:
    calls: int = 0
    retries: int = 0
    pauses: int = 0
    consecutive_429: int = 0


class RateLimiter:
    def __init__(
        self,
        max_concurrency: int = 5,
        jitter: float = 0.2,
        max_retries: int = 5,
        pause_threshold: int = 5,
        pause_seconds: float = 60.0,
    ):
        self.max_concurrency = max(1, max_concurrency)
        self.jitter = jitter
        self.max_retries = max_retries
        self.pause_threshold = pause_threshold
        self.pause_seconds = pause_seconds
        self._semaphore = asyncio.Semaphore(self.max_concurrency)
        self.stats = RateLimitStats()
        self._lock = asyncio.Lock()

    async def run(self, func: Callable[[], Awaitable[T]], label: str = "") -> T:
        async with self._semaphore:
            return await self._run_with_retry(func, label)

    async def _run_with_retry(self, func: Callable[[], Awaitable[T]], label: str) -> T:
        attempt = 0
        while True:
            try:
                result = await func()
                async with self._lock:
                    self.stats.calls += 1
                    self.stats.consecutive_429 = 0
                if self.jitter:
                    await asyncio.sleep(random.uniform(0, self.jitter * 0.05))
                return result
            except discord.HTTPException as exc:
                status = getattr(exc, "status", None)
                if status == 429:
                    async with self._lock:
                        self.stats.retries += 1
                        self.stats.consecutive_429 += 1
                        consecutive = self.stats.consecutive_429
                    retry_after = getattr(exc, "retry_after", None)
                    delay = float(retry_after) if retry_after else min(2 ** attempt, 30)
                    delay += random.uniform(0, delay * self.jitter)
                    log.warning("429 on %s; sleeping %.2fs", label, delay)
                    await asyncio.sleep(delay)
                    if consecutive >= self.pause_threshold:
                        async with self._lock:
                            self.stats.pauses += 1
                            self.stats.consecutive_429 = 0
                        log.warning("Consecutive 429 threshold reached; pausing %.2fs", self.pause_seconds)
                        await asyncio.sleep(self.pause_seconds)
                    attempt += 1
                    if attempt > self.max_retries:
                        raise
                    continue
                if status is not None and 500 <= status < 600 and attempt < self.max_retries:
                    delay = min(2 ** attempt, 30) + random.uniform(0, 1)
                    log.warning("HTTP %s on %s; retrying in %.2fs", status, label, delay)
                    await asyncio.sleep(delay)
                    attempt += 1
                    continue
                raise
            except (OSError, asyncio.TimeoutError) as exc:
                if attempt < self.max_retries:
                    delay = min(2 ** attempt, 30) + random.uniform(0, 1)
                    log.warning("Network error on %s: %s; retrying in %.2fs", label, exc, delay)
                    await asyncio.sleep(delay)
                    attempt += 1
                    continue
                raise

    async def map(self, items: list, func: Callable[[object], Awaitable[T]], label: str = "") -> list[T | BaseException]:
        results: list[T | BaseException] = []
        async def worker(item: object) -> T:
            return await self.run(lambda: func(item), f"{label}:{item}")
        tasks = [asyncio.create_task(worker(item)) for item in items]
        for task in asyncio.as_completed(tasks):
            try:
                results.append(await task)
            except Exception as exc:  # noqa: BLE001
                results.append(exc)
        return results
