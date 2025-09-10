"""
Created by Michael Wilson, Senior Software Engineer
9/09/2025
"""

from __future__ import annotations
import json, logging
from typing import Any, Dict, Optional, Callable, Awaitable
import websockets
from .config import MichaelConfig
from .gql import SUB_DETECTIONS

LOG = logging.getLogger("michael")

class michaelubs:
    def __init__(self, cfg: MichaelConfig):
        self.cfg = cfg

    async def detections(
        self,
        on_item: Callable[[Dict[str, Any]], Awaitable[None]],
        device_id: Optional[str] = None,
        detection_type: Optional[str] = None,
        min_confidence: float = 0.5,
    ):
        variables = {
            "deviceId": device_id,
            "detectionType": detection_type,
            "minConfidence": min_confidence,
        }
        variables = {k: v for k, v in variables.items() if v is not None}

        async with websockets.connect(
            self.cfg.ws_url,
            subprotocols=["graphql-transport-ws"],
        ) as ws:
            # Init
            await ws.send(json.dumps({"type": "connection_init", "payload": {
                "x-token-id": self.cfg.token_id,
                "x-token-value": self.cfg.token_value,
            }}))

            # Expect ack
            while True:
                msg = json.loads(await ws.recv())
                if msg.get("type") == "connection_ack":
                    break

            # Subscribe
            await ws.send(json.dumps({
                "id": "1",
                "type": "subscribe",
                "payload": {"query": SUB_DETECTIONS, "variables": variables},
            }))

            LOG.info("Listening for detections (min_confidence=%.2f)...", min_confidence)
            async for raw in ws:
                evt = json.loads(raw)
                if evt.get("type") == "next":
                    payload = evt.get("payload", {}).get("data", {})
                    det = payload.get("detectionCreated")
                    if det:
                        await on_item(det)
                elif evt.get("type") in ("error", "complete"):
                    LOG.info("Subscription finished: %s", evt.get("type"))
                    break
