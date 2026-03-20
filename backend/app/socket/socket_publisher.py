import asyncio
from typing import Any

from app.socket.socket_events import make_envelope
from app.socket.socket_manager import connection_manager


async def publish(event: str, payload: Any = None) -> None:
    message = make_envelope(event, payload)
    await connection_manager.broadcast_json(message)


def publish_best_effort(event: str, payload: Any = None) -> None:
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        try:
            asyncio.run(publish(event, payload))
        except Exception:
            pass
        return

    async def _publish_safely() -> None:
        try:
            await publish(event, payload)
        except Exception:
            pass

    loop.create_task(_publish_safely())
