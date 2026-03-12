from typing import Any

from app.socket.socket_manager import connection_manager


async def publish(event: str, payload: dict[str, Any] | None = None) -> None:
    message: dict[str, Any] = {
        "event": event,
        "payload": payload or {},
    }
    await connection_manager.broadcast_json(message)
