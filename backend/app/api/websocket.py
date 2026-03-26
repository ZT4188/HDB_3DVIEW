"""
WebSocket endpoint — pushes yearly simulation tick events to connected clients.
"""

import asyncio
import json
import redis.asyncio as aioredis
import os

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

router = APIRouter()

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
WS_CHANNEL_PREFIX = "sim:tick:"


@router.websocket("/ws/sessions/{session_id}")
async def simulation_websocket(websocket: WebSocket, session_id: str):
    """
    Clients connect here to receive real-time yearly tick events.

    Each tick message has the shape:
    {
      "type": "tick",
      "year": 2026,
      "total_residents": 1234567,
      "total_births": 12000,
      "total_deaths": 7500,
      "resident_deltas": {"building_id": delta, ...},
      "move_log": [{"from_id": "...", "to_id": "...", "count": 12}, ...]
    }
    """
    await websocket.accept()

    redis = aioredis.from_url(REDIS_URL)
    pubsub = redis.pubsub()
    channel = f"{WS_CHANNEL_PREFIX}{session_id}"
    await pubsub.subscribe(channel)

    try:
        async for message in pubsub.listen():
            if message["type"] == "message":
                data = json.loads(message["data"])
                await websocket.send_json(data)
    except WebSocketDisconnect:
        pass
    finally:
        await pubsub.unsubscribe(channel)
        await redis.aclose()
