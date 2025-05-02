#####################################################################################################

import logging
from typing import Any, Final
from fastapi import WebSocket, APIRouter, WebSocketDisconnect


from services.voice_service import VoiceAssistant

#####################################################################################################

router: Final = APIRouter(tags=['WS'], prefix='/api/ws')

#####################################################################################################

class ConnectionManager:
    def __init__(self):
        self.active_connections: dict[WebSocket, VoiceAssistant] = {}
        self.logger = logging.getLogger(__name__)
    
    async def connect_client(self, websocket: WebSocket) -> VoiceAssistant:
        await websocket.accept()
        # Connect to voice service
        voice_service = VoiceAssistant(
            app_settings=websocket.app.app_settings,
            xano_service=websocket.app.xano_service,
            client_ws=websocket,
            logger=websocket.app.logger,
        )
        self.active_connections[websocket] = voice_service
        self.logger.info('Client connected')
        return voice_service
    
    async def disconnect_client(self, websocket: WebSocket):
        if websocket in self.active_connections:
            voice_service = self.active_connections[websocket]
            await voice_service.finish()
            del self.active_connections[websocket]
            self.logger.info('Client disconnected')

    async def send_to_client(self, websocket: WebSocket, data: Any):
        await websocket.send_json(data) if isinstance(data, dict) else await websocket.send_bytes(data)
    
    async def send_to_voice_service(self, websocket: WebSocket, data: Any):
        if websocket not in self.active_connections:
            print("Client not found in active connections")
            return False
        voice_service = self.active_connections[websocket]
        await voice_service.dg_connection.send(data)

#####################################################################################################

manager = ConnectionManager()

#####################################################################################################

@router.websocket("")
async def websocket_endpoint(websocket: WebSocket) -> None:
    voice_assistant = None
    manager.logger.info('New client connection attempt')
    try:
        voice_assistant = await manager.connect_client(websocket)
        await voice_assistant.run()
    except WebSocketDisconnect:
        manager.logger.info("Client closed connection")
    except Exception as e:
        manager.logger.error(f"Error in websocket connection", exc_info=e)
    finally:
        if voice_assistant:
            await manager.disconnect_client(websocket)

#####################################################################################################
