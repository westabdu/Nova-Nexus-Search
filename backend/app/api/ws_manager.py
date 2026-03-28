"""
WebSocket Manager - FastAPI WebSocket ile canlı ilerleme mesajları iletir.
Flet tarafında da Pub/Sub benzer bir pattern kullanılacak.
"""
from fastapi import WebSocket
from loguru import logger
import asyncio
from typing import Dict

class ConnectionManager:
    """Birden fazla WebSocket bağlantısını yönetir."""
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}

    async def connect(self, session_id: str, websocket: WebSocket):
        await websocket.accept()
        self.active_connections[session_id] = websocket
        logger.info(f"WebSocket connected: {session_id}")

    async def disconnect(self, session_id: str):
        if session_id in self.active_connections:
            ws = self.active_connections.pop(session_id)
            try:
                await ws.close(code=1000)
            except Exception:
                pass
            logger.info(f"WebSocket disconnected: {session_id}")

    async def send_progress(self, session_id: str, message: str):
        """Belirli bir session'a mesaj gönder."""
        websocket = self.active_connections.get(session_id)
        if websocket:
            try:
                await websocket.send_json({"type": "progress", "message": message})
            except Exception as e:
                logger.error(f"WS send_progress error for {session_id}: {e}")
                await self.disconnect(session_id)

    async def send_result(self, session_id: str, data: dict):
        """Araştırma tamamlandığında final raporu gönder."""
        websocket = self.active_connections.get(session_id)
        if websocket:
            try:
                await websocket.send_json({"type": "result", "data": data})
            except Exception as e:
                logger.error(f"WS send_result error for {session_id}: {e}")
                await self.disconnect(session_id)

    async def send_error(self, session_id: str, error: str):
        """Hata mesajı gönder."""
        websocket = self.active_connections.get(session_id)
        if websocket:
            try:
                await websocket.send_json({"type": "error", "message": error})
            except Exception as e:
                logger.error(f"WS send_error error {session_id}: {e}")

manager = ConnectionManager()
