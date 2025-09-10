"""
Created by Michael Wilson, Senior Software Engineer
"""

from __future__ import annotations
import asyncio, json, logging
from typing import Any, Dict, Optional
import aiohttp
from .config import MichaelConfig

LOG = logging.getLogger("michael")

class MichaelHTTP:
    def __init__(self, cfg: MichaelConfig):
        self.cfg = cfg
        self._session: Optional[aiohttp.ClientSession] = None

    async def __aenter__(self) -> "MichaelHTTP":
        timeout = aiohttp.ClientTimeout(total=self.cfg.request_timeout_s)
        self._session = aiohttp.ClientSession(
            timeout=timeout,
            headers={
                "Content-Type": "application/json",
                "x-token-id": self.cfg.token_id,
                "x-token-value": self.cfg.token_value,
            },
        )
        return self

    async def __aexit__(self, *exc):
        if self._session:
            await self._session.close()

    async def execute(self, query: str, variables: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        if not self._session:
            raise RuntimeError("Session not initialized")

        payload = {"query": query}
        if variables:
            payload["variables"] = variables

        attempt = 0
        backoff = self.cfg.retry_backoff_s
        while True:
            attempt += 1
            try:
                async with self._session.post(self.cfg.api_url, json=payload) as resp:
                    resp.raise_for_status()
                    data = await resp.json()
                if "errors" in data:
                    LOG.warning("GraphQL returned errors: %s", data["errors"][:1])
                return data
            except Exception as e:
                if attempt > self.cfg.retries:
                    raise
                await asyncio.sleep(backoff)
                backoff *= 2
                LOG.debug("Retrying after error (%s), attempt %d", e, attempt)
