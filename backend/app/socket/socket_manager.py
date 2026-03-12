from typing import Any

from fastapi import WebSocket


class ConnectionManager:
    def __init__(self) -> None:
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket) -> None:
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket) -> None:
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def send_json(self, websocket: WebSocket, message: dict[str, Any]) -> None:
        await websocket.send_json(message)

    async def broadcast_json(self, message: dict[str, Any]) -> None:
        disconnected: list[WebSocket] = []

        for connection in list(self.active_connections):
            try:
                await self.send_json(connection, message)
            except Exception:
                disconnected.append(connection)

        for connection in disconnected:
            self.disconnect(connection)


connection_manager = ConnectionManager()
