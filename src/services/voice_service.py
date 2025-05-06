#####################################################################################################
import json
from datetime import datetime
from logging import Logger
from pathlib import Path

from fastapi import WebSocketDisconnect
from deepgram import (
    DeepgramClient,
    AsyncAgentWebSocketClient,
    AgentWebSocketEvents,
    SettingsConfigurationOptions,
    FunctionCallRequest,
    DeepgramClientOptions,
    Agent,
    Think,
    Provider,
    Speak,
    Audio,
    Output,
    Input, Context,
)
from deepgram.utils import verboselogs
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.websockets import WebSocket, WebSocketState

from commands.commands import (
    CreateAppointmentCommand,
    EndCallCommand,
    GetFreeCalendarSlotsCommand,
    SearchPropertiesCommand,
)
from configs.settings import AppSettings
from schema.client import ClientJsonMessage
from services.agency import AgencyService
from services.func_tools import FUNCTION_DEFINITIONS
from services.xano import XanoService

#####################################################################################################

class VoiceAssistant:
    def __init__(
        self,
        app_settings: AppSettings,
        client_ws: WebSocket,
        xano_service: XanoService,
        logger: Logger,
        db_session: AsyncSession,
    ) -> None:
        self._app_settings = app_settings
        self._xano_service = xano_service
        self.client_ws = client_ws
        self._agency_service = AgencyService(session=db_session)

        # TODO init it later to set up micro and speaker.
        config: DeepgramClientOptions = DeepgramClientOptions(
            options={
                "keepalive": "true",
                "microphone_record": "false",
                "speaker_playback": "false",
            },
            verbose=verboselogs.WARNING,
        )
        self.deepgram_client = DeepgramClient(app_settings.deepgram_api_key, config)
        self._instructions_path = Path(__file__).parent.parent / 'prompts' / 'dev_instructions.txt'
        self.dg_connection: AsyncAgentWebSocketClient | None = None
        self._is_client_active = None
        self._logger = logger

    async def _process_bytes_message(self, data: bytes) -> None:
        if self.dg_connection:
            is_send = await self.dg_connection.send(data)

    async def _get_configuration_options(self, agency_id: str | None, dev_mode: bool = False) -> SettingsConfigurationOptions:
        if dev_mode and self._app_settings.dev_mode:
            # return dev mode options
            agent = Agent(
                think=Think(
                    provider=Provider(
                        type='open_ai',
                    ),
                    model='gpt-4o-mini',
                    instructions=self._instructions_path.read_text().format(now=datetime.now()),
                    functions=FUNCTION_DEFINITIONS,
                ),
                speak=Speak(
                    # model="aura-2-pandora-en",
                    model=None,
                    provider='eleven_labs',
                    # voice_id='XW70ikSsadUbinwLMZ5w',
                    voice_id='SB13jgWjPxi4e4JoTT1H',
                )
            )
            audio = Audio(
                input=Input(
                    encoding='linear32',
                    sample_rate=48000,
                ),
                output=Output(
                    encoding='linear16',
                    sample_rate=24000,
                    container='none',
                )
            )
            context = Context(
                messages=[
                    {
                        "role": "assistant",
                        "content": "Welcome to Pacitti Jones. I’m Margaret, your AI assistant."
                                   " How may I help you today?"
                    },
                ],
                replay=True
            )
            return SettingsConfigurationOptions(agent=agent, audio=audio, context=context)
        else:
            settings = await self._agency_service.get_agency_configuration(agency_id)
            return SettingsConfigurationOptions.from_dict(settings)

    async def _on_start(self, message: ClientJsonMessage) -> None:
        self.dg_connection: AsyncAgentWebSocketClient = self.deepgram_client.agent.asyncwebsocket.v("1")
        self._register_handlers()
        options = await self._get_configuration_options(message.client_id, message.dev_mode)
        if await self.dg_connection.start(options) is False:
            await self.client_ws.send_json(data={"type": "error", "detail": "error on startup deepgram connection"})
        else:
            await self.client_ws.send_json(data={"type": "settings_applied"})

    async def _on_finish(self) -> None:
        await self.finish()

    async def _process_json_message(self, message: ClientJsonMessage) -> None:
        if message.type == "start":
            await self._on_start(message)
        elif message.type == "finish":
            self._logger.info('Client send finish message')
            await self._on_finish()
        else:
            # TODO Implement interaction with agency service
            self._logger.warning(f'Received unknown message type from client: "{message.type}"')
            await self.client_ws.send_json({'type': 'error', "detail": f'Unknown message type: {message.type}'})

    async def _handle_client_message(self) -> None:
        message = await self.client_ws.receive()
        self.client_ws._raise_on_disconnect(message)
        if "bytes" in message and message["bytes"] is not None:
            data = message['bytes']
            await self._process_bytes_message(data)
        elif "text" in message and message["text"] is not None:
            try:
                client_message = ClientJsonMessage.model_validate_json(message["text"])
                await self._process_json_message(client_message)
            except ValidationError:
                await self.client_ws.send_json({"type": "error", "detail": 'Wrong message format'})
            except Exception as e:
                self._logger.error('Error when processing text message', exc_info=e)
                await self.client_ws.send_json({"type": "error", "detail": "Unknown error occurred"})

    async def run(self) -> None:
        if self.client_ws.client_state == WebSocketState.CONNECTED:
            self._is_client_active = True
        while self._is_client_active:
            try:
                await self._handle_client_message()
            except WebSocketDisconnect:
                print('WebsocketDisconnect')
                if self.dg_connection and await self.dg_connection.is_connected():
                    await self.finish()
                self._is_client_active = False
                print('Gracefully disconnected')

    def _get_actual_instructions(self) -> str:
        # TODO return depending on time zone
        return self._instructions_path.read_text().format(now=datetime.now())

    async def finish(self) -> bool:
        # self._is_client_active = False
        if self.dg_connection:
            is_finished = await self.dg_connection.finish()
            self.dg_connection = None
            return is_finished

    def _register_handlers(self):
        async def on_open(deepgram_agent, open, **kwargs):
            print(f"\n\n{open}\n\n")

        async def on_binary_data(deepgram_agent, data, **kwargs):
            await self.client_ws.send_bytes(data)

        async def on_welcome(deepgram_agent, welcome, **kwargs):
            print(f"\n\n{welcome}\n\n")

        async def on_settings_applied(deepgram_agent, settings_applied, **kwargs):
            print(f"\n\n{settings_applied}\n\n")

        async def on_conversation_text(deepgram_agent, conversation_text, **kwargs):
            d = True
            await self.client_ws.send_text(conversation_text.to_json(indent=4))

        async def on_user_started_speaking(deepgram_agent, user_started_speaking, **kwargs):
            await self.client_ws.send_text(user_started_speaking.to_json())

        async def on_agent_thinking(deepgram_agent, agent_thinking, **kwargs):
            print(f"\n\n{agent_thinking}\n\n")

        async def on_function_calling(deepgram_agent, function_calling, **kwargs):
            if self._app_settings.dev_mode:
                await self.client_ws.send_text(function_calling.to_json())

        async def on_function_call(
            deepgram_agent: AsyncAgentWebSocketClient,
            function_call_request: FunctionCallRequest,
            **kwargs,
        ) -> None:
            self._logger.debug(f'Function call name: "{function_call_request.function_name}" received with params: {function_call_request.input}')
            if not function_call_request.input:
                await deepgram_agent.send(json.dumps({"error": "No input data provided for function call."}))
            cmd_name = function_call_request.function_name
            command_args = {
                "xano_service": self._xano_service,
                "logger": self._logger,
                "client_ws": self.client_ws,
                "deepgram_agent": deepgram_agent,
                "dev_mode": self._app_settings.dev_mode,
            }
            match cmd_name:
                case 'searchForProperties':
                    cmd = SearchPropertiesCommand(**command_args)
                    await cmd.execute(function_call_request)
                case 'getFreeCalendarSlots':
                    cmd = GetFreeCalendarSlotsCommand(**command_args)
                    await cmd.execute(function_call_request)
                case 'createAppointment':
                    cmd = CreateAppointmentCommand(**command_args)
                    await cmd.execute(function_call_request)
                case 'end_call':
                    cmd = EndCallCommand(exit_callback=self.finish, **command_args)
                    await cmd.execute(function_call_request)
                case _:
                    self._logger.warning(f'Unknown function call: "{cmd_name}"')
                    await deepgram_agent.send(json.dumps({"error": f"Unknown function call: {cmd_name}"}))
                
        async def on_agent_started_speaking(deepgram_agent, agent_started_speaking, **kwargs):
            print(f"\n\n{agent_started_speaking}\n\n")

        async def on_agent_audio_done(deepgram_agent, agent_audio_done, **kwargs):
            print(f"\n\n{agent_audio_done}\n\n")

        async def on_close(deepgram_agent, close, **kwargs):
            print(f"\n\n{close}\n\n")

        async def on_error(deepgram_agent, error, **kwargs):
            print(f"\n\n{error}\n\n")

        async def on_unhandled(deepgram_agent, unhandled, **kwargs):
            try:
                data = json.loads(unhandled['raw'])
                if data.get('type') == "EndOfThought":
                    print("EndOfThought received")
            except Exception as ex:
                print(f"\n\n{unhandled}\n\n")

        self.dg_connection.on(AgentWebSocketEvents.Open, on_open)
        self.dg_connection.on(AgentWebSocketEvents.AudioData, on_binary_data)
        self.dg_connection.on(AgentWebSocketEvents.Welcome, on_welcome)
        self.dg_connection.on(AgentWebSocketEvents.SettingsApplied, on_settings_applied)
        self.dg_connection.on(AgentWebSocketEvents.ConversationText, on_conversation_text)
        self.dg_connection.on(
            AgentWebSocketEvents.UserStartedSpeaking, on_user_started_speaking
        )
        self.dg_connection.on(AgentWebSocketEvents.AgentThinking, on_agent_thinking)
        self.dg_connection.on(AgentWebSocketEvents.FunctionCalling, on_function_calling)
        self.dg_connection.on(AgentWebSocketEvents.FunctionCallRequest, on_function_call)
        self.dg_connection.on(
            AgentWebSocketEvents.AgentStartedSpeaking, on_agent_started_speaking
        )
        self.dg_connection.on(AgentWebSocketEvents.AgentAudioDone, on_agent_audio_done)
        self.dg_connection.on(AgentWebSocketEvents.Close, on_close)
        self.dg_connection.on(AgentWebSocketEvents.Error, on_error)
        self.dg_connection.on(AgentWebSocketEvents.Unhandled, on_unhandled)

#####################################################################################################
