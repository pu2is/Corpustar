from typing import Any

from app.socket.socket_events import make_envelope
from app.socket.socket_manager import connection_manager


async def publish(event: str, payload: dict[str, Any] | None = None) -> None:
    message = make_envelope(event, payload)
    await connection_manager.broadcast_json(message)
