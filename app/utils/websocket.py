from fastapi import WebSocket, WebSocketDisconnect
from typing import Dict, List
import json
import logging
from bson import ObjectId

class ConnectionManager:
    """Manage WebSocket connections for real-time communication"""
    
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.user_connections: Dict[str, List[str]] = {}

    async def connect(self, websocket: WebSocket, user_id: str, connection_id: str):
        """Accept a new WebSocket connection"""
        await websocket.accept()
        self.active_connections[connection_id] = websocket
        if user_id not in self.user_connections:
            self.user_connections[user_id] = []
        self.user_connections[user_id].append(connection_id)
        logging.info(f"New connection: {connection_id} for user {user_id}")

    def disconnect(self, connection_id: str):
        """Remove a WebSocket connection"""
        if connection_id in self.active_connections:
            del self.active_connections[connection_id]
            for user_id, connections in self.user_connections.items():
                if connection_id in connections:
                    connections.remove(connection_id)
                    if not connections:
                        del self.user_connections[user_id]
                    break
            logging.info(f"Connection closed: {connection_id}")

    async def send_personal_message(self, message: dict, user_id: str):
        """Send a message to a specific user"""
        if user_id in self.user_connections:
            for connection_id in self.user_connections[user_id]:
                if connection_id in self.active_connections:
                    try:
                        await self.active_connections[connection_id].send_json(message)
                    except Exception as e:
                        logging.error(f"Error sending message to {connection_id}: {e}")
                        self.disconnect(connection_id)

    async def broadcast(self, message: dict):
        """Send a message to all connected clients"""
        for connection_id, websocket in self.active_connections.items():
            try:
                await websocket.send_json(message)
            except Exception as e:
                logging.error(f"Error broadcasting to {connection_id}: {e}")
                self.disconnect(connection_id)

def serialize_for_websocket(data):
    """Convert MongoDB documents to JSON-serializable format"""
    if isinstance(data, (list, tuple)):
        return [serialize_for_websocket(item) for item in data]
    elif isinstance(data, dict):
        return {key: serialize_for_websocket(value) for key, value in data.items()}
    elif isinstance(data, ObjectId):
        return str(data)
    elif hasattr(data, 'isoformat'):
        return data.isoformat()
    else:
        return data