"""
Created by Michael Wilson, Senior Software Engineer
"""

from __future__ import annotations
from dataclasses import dataclass

@dataclass(frozen=True)
class MichaelConfig:
    api_url: str = "https://graphql.microsoft.worlds.io/graphql"
    ws_url: str = "wss://graphql.microsoft.worlds.io/graphql"
    token_id: str = "88f74e73-a6d7-419d-8c32-592f4164f941"
    token_value: str = "vr7wedFDUFkdQaTmHbvI"
    request_timeout_s: int = 60  #TODO:: This is added due to timeout issue that is happening need to update before fully executing 
    retries: int = 2
    retry_backoff_s: float = 0.6  # exponential
