from datetime import datetime
from logging import Logger
from pathlib import Path

from deepgram import DeepgramClient, AsyncAgentWebSocketClient, AgentWebSocketEvents, SettingsConfigurationOptions, \
    FunctionCallRequest, DeepgramClientOptions, Agent, Think, Provider, FunctionCallResponse, Speak
from deepgram.utils import verboselogs
from starlette.websockets import WebSocket, WebSocketDisconnect, WebSocketState

from configs.settings import AppSettings
from services.func_tools import FUNCTION_DEFINITIONS, FunctionCallHandler
from services.xano import XanoService


class VoiceAssistant:
    def __init__(
        self,
        app_settings: AppSettings,
        client_ws: WebSocket,
        xano_service: XanoService,
        logger: Logger,
    ) -> None:
        self.function_call_handler: FunctionCallHandler = FunctionCallHandler(xano_service)
        self.client_ws = client_ws

        # TODO init it later to set up micro and speaker.
        config: DeepgramClientOptions = DeepgramClientOptions(
            options={
                "keepalive": "true",
                "microphone_record": "true",
                "speaker_playback": "true",
            },
            verbose=verboselogs.WARNING,
        )
        self.deepgram_client = DeepgramClient(app_settings.deepgram_api_key, config)
        self._instructions_path = Path(__file__).parent.parent / 'prompts' / 'dev_instructions.txt'
        self.dg_connection: AsyncAgentWebSocketClient | None = None
        self._is_client_active = None
        self._logger = logger

    async def run(self):
        if self.client_ws.client_state == WebSocketState.CONNECTED:
            self._is_client_active = True
        while self._is_client_active:
            try:
                print('before client message')
                data = await self.client_ws.receive_json()
                print('after client message')
                if data.get("type") == "start":
                    self.dg_connection: AsyncAgentWebSocketClient = self.deepgram_client.agent.asyncwebsocket.v("1")
                    self._register_handlers()
                    options = data.get("options")
                    # TODO Del hardcode
                    if options is None:
                        agent = Agent(
                            think=Think(
                                provider=Provider(
                                    type='open_ai'
                                ),
                                model='gpt-4o-mini',
                                instructions=self._instructions_path.read_text().format(now=datetime.now()),
                                functions=FUNCTION_DEFINITIONS,
                            ),
                            speak=Speak(
                                model=None,  # As I understand they use ElevenLabs’ Turbo 2.5
                                provider='eleven_labs',
                                voice_id='GItJI30LSRkzJQjuHqkk',
                                # voice_id='XW70ikSsadUbinwLMZ5w',
                                # voice_id='eVItLK1UvXctxuaRV2Oq',
                                # voice_id='MzqUf1HbJ8UmQ0wUsx2p',
                            )
                        )
                        options = SettingsConfigurationOptions(agent=agent)
                    if await self.dg_connection.start(options) is False:
                        print("Failed to start connection")
                        return
                elif data.get("type") == "stop":
                    await self.finish()
                else:
                    print(f"Unknown message type: {data.get('type')}")
            except WebSocketDisconnect:
                print('WebsocketDisconnect')
                if self.dg_connection and await self.dg_connection.is_connected():
                    await self.finish()
                self._is_client_active = False

    def _get_actual_instructions(self) -> str:
        # TODO return depending on time zone
        return self._instructions_path.read_text().format(now=datetime.now())

    async def finish(self) -> bool:
        # self._is_client_active = False
        if self.dg_connection:
            return await self.dg_connection.finish()

    def _register_handlers(self):
        async def on_open(deepgram_agent, open, **kwargs):
            print(f"\n\n{open}\n\n")

        async def on_binary_data(deepgram_agent, data, **kwargs):
            global warning_notice
            if warning_notice:
                print("Received binary data")
                print("You can do something with the binary data here")
                warning_notice = False

        async def on_welcome(deepgram_agent, welcome, **kwargs):
            print(f"\n\n{welcome}\n\n")

        async def on_settings_applied(deepgram_agent, settings_applied, **kwargs):
            print(f"\n\n{settings_applied}\n\n")

        async def on_conversation_text(deepgram_agent, conversation_text, **kwargs):
            d = True
            print(f'conversation_text: {conversation_text}')
            await self.client_ws.send_text(conversation_text.to_json(indent=4))

        async def on_user_started_speaking(deepgram_agent, user_started_speaking, **kwargs):
            print(f"\n\n{user_started_speaking}\n\n")

        async def on_agent_thinking(deepgram_agent, agent_thinking, **kwargs):
            print(f"\n\n{agent_thinking}\n\n")

        async def on_function_calling(deepgram_agent, function_calling, **kwargs):
            print(f"\n\nFUNCTION CALLING WAS TRIGGERED!\n\n")

        async def on_function_call(
            deepgram_agent: AsyncAgentWebSocketClient,
            function_call_request: FunctionCallRequest,
            **kwargs,
        ) -> None:
            self._logger.debug('Function call handler start working')
            result = await self.function_call_handler.handle_function_call(function_call_request)
            response = FunctionCallResponse(
                function_call_id=function_call_request.function_call_id,
                output=result
            )
            self._logger.debug(f'Function call handler result: {response}')
            await deepgram_agent.send(response.to_json(ensure_ascii=False, indent=4))
            
        async def on_agent_started_speaking(deepgram_agent, agent_started_speaking, **kwargs):
            print(f"\n\n{agent_started_speaking}\n\n")

        async def on_agent_audio_done(deepgram_agent, agent_audio_done, **kwargs):
            print(f"\n\n{agent_audio_done}\n\n")

        async def on_close(deepgram_agent, close, **kwargs):
            print(f"\n\n{close}\n\n")

        async def on_error(deepgram_agent, error, **kwargs):
            print(f"\n\n{error}\n\n")

        async def on_unhandled(deepgram_agent, unhandled, **kwargs):
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





