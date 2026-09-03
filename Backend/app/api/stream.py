"""Real-time Server-Sent Events (SSE) telemetry streaming endpoints."""

from __future__ import annotations

import asyncio
import json
import logging
from typing import AsyncGenerator

from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse
from sse_starlette.sse import EventSourceResponse

from app.services.detector import analyse_telemetry, get_open_incidents
from app.simulator.telemetry import generate_normal_telemetry

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["streaming"])


async def telemetry_event_generator(
    satellite_id: str,
    request: Request,
    interval_seconds: float = 1.0,
) -> AsyncGenerator[dict, None]:
    """Generate live telemetry SSE events every 1 second until client disconnects."""
    logger.info("Client connected to live telemetry stream for %s", satellite_id)
    try:
        while True:
            # Check if client disconnected
            if await request.is_disconnected():
                logger.info("Client disconnected from telemetry stream for %s", satellite_id)
                break

            # 1. Generate live telemetry reading
            snapshot = generate_normal_telemetry(satellite_id)

            # 2. Run deterministic anomaly detection
            anomalies = analyse_telemetry(snapshot)

            # 3. Package SSE data payload
            payload = {
                "satellite_id": satellite_id,
                "timestamp": snapshot["timestamp"],
                "metrics": snapshot["metrics"],
                "anomalies_detected": [a.model_dump(mode="json") for a in anomalies],
                "open_incidents_count": len(get_open_incidents()),
            }

            yield {
                "event": "telemetry",
                "data": json.dumps(payload),
            }

            await asyncio.sleep(interval_seconds)
    except asyncio.CancelledError:
        logger.info("Telemetry stream cancelled for %s", satellite_id)


@router.get("/stream/telemetry/{satellite_id}")
async def stream_telemetry(
    satellite_id: str,
    request: Request,
) -> EventSourceResponse:
    """Stream live 1Hz telemetry snapshots and real-time anomaly alerts via Server-Sent Events (SSE).

    Frontend clients can connect using standard HTML5 EventSource:
    ```javascript
    const source = new EventSource('/api/stream/telemetry/SAT-01');
    source.addEventListener('telemetry', (e) => {
      const data = JSON.parse(e.data);
      console.log('Live telemetry:', data);
    });
    ```
    """
    return EventSourceResponse(
        telemetry_event_generator(satellite_id, request, interval_seconds=1.0)
    )
