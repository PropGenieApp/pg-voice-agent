#####################################################################################################
import os
from dotenv import load_dotenv
from datetime import datetime
from pathlib import Path
import asyncio

from deepgram.clients.agent.v1 import Agent
from deepgram.utils import verboselogs

from deepgram import (
    DeepgramClient,
    DeepgramClientOptions,
    AgentWebSocketEvents,
    SettingsConfigurationOptions, Think, Provider, FunctionCallRequest, FunctionCallResponse, AsyncAgentWebSocketClient,
)

from configs.logger import setup_logging
from configs.settings import AppSettings
from services.func_tools import FUNCTION_DEFINITIONS, FunctionCallHandler
from services.xano import XanoService
from utils.aiohttp_utils import create_aiohttp_client

#####################################################################################################

load_dotenv()

logger = setup_logging()

warning_notice = True

API_KEY = os.getenv('DEEPGRAM_API_KEY')
if not API_KEY:
    print('provide "DEEPGRAM_API_KEY" variable')
    exit(1)

INSTRUCTIONS_PATH = Path(__file__).parent / 'prompts' / 'dev_instructions.txt'

async def main():
    try:
        app_settings = AppSettings()
        client = create_aiohttp_client()
        xano_service = XanoService(
            app_settings=app_settings,
            aiohttp_client=client,
            logger=logger,
        )
        function_call_handler = FunctionCallHandler(xano_service)
        # uow_services = InternalAppServices(xano_service)

        # example of setting up a client config. logging values: WARNING, VERBOSE, DEBUG, SPAM
        config: DeepgramClientOptions = DeepgramClientOptions(
            options={
                "keepalive": "true",
                "microphone_record": "true",
                "speaker_playback": "true",
            },
            verbose=verboselogs.WARNING,
        )
        deepgram: DeepgramClient = DeepgramClient("f6c6ded5a3dba84bedd08ffd04188fcdcad81f93", config)

        # Create a websocket connection to Deepgram
        dg_connection: AsyncAgentWebSocketClient = deepgram.agent.asyncwebsocket.v("1")

        async def on_open(self, open, **kwargs):
            print(f"\n\n{open}\n\n")

        async def on_binary_data(self, data, **kwargs):
            global warning_notice
            if warning_notice:
                print("Received binary data")
                print("You can do something with the binary data here")
                warning_notice = False

        async def on_welcome(self, welcome, **kwargs):
            print(xano_service)
            print(f"\n\n{welcome}\n\n")

        async def on_settings_applied(self, settings_applied, **kwargs):
            print(f"\n\n{settings_applied}\n\n")

        async def on_conversation_text(self, conversation_text, **kwargs):
            print(f"\n\n{conversation_text}\n\n")

        async def on_user_started_speaking(self, user_started_speaking, **kwargs):
            print(f"\n\n{user_started_speaking}\n\n")

        async def on_agent_thinking(self, agent_thinking, **kwargs):
            print(f"\n\n{agent_thinking}\n\n")

        async def on_function_calling(self, function_calling, **kwargs):
            print(f"\n\nFUNCTION CALLING WAS TRIGGERED!\n\n")

        async def on_function_call(
            self: AsyncAgentWebSocketClient,
            function_call_request: FunctionCallRequest,
            **kwargs,
        ):
            result = await function_call_handler.handle_function_call(function_call_request)

            response = FunctionCallResponse(
                function_call_id=function_call_request.function_call_id,
                output=result  # result.model_dump() / to_dict(result)
            )
            print(response)
            str_response = str(response)
            debug = True
            await self.send(str_response)

        async def on_agent_started_speaking(self, agent_started_speaking, **kwargs):
            print(f"\n\n{agent_started_speaking}\n\n")

        async def on_agent_audio_done(self, agent_audio_done, **kwargs):
            print(f"\n\n{agent_audio_done}\n\n")

        async def on_close(self, close, **kwargs):
            print(f"\n\n{close}\n\n")

        async def on_error(self, error, **kwargs):
            print(f"\n\n{error}\n\n")

        async def on_unhandled(self, unhandled, **kwargs):
            print(f"\n\n{unhandled}\n\n")

        dg_connection.on(AgentWebSocketEvents.Open, on_open)
        dg_connection.on(AgentWebSocketEvents.AudioData, on_binary_data)
        dg_connection.on(AgentWebSocketEvents.Welcome, on_welcome)
        dg_connection.on(AgentWebSocketEvents.SettingsApplied, on_settings_applied)
        dg_connection.on(AgentWebSocketEvents.ConversationText, on_conversation_text)
        dg_connection.on(
            AgentWebSocketEvents.UserStartedSpeaking, on_user_started_speaking
        )
        dg_connection.on(AgentWebSocketEvents.AgentThinking, on_agent_thinking)
        dg_connection.on(AgentWebSocketEvents.FunctionCalling, on_function_calling)
        dg_connection.on(AgentWebSocketEvents.FunctionCallRequest, on_function_call)
        dg_connection.on(
            AgentWebSocketEvents.AgentStartedSpeaking, on_agent_started_speaking
        )
        dg_connection.on(AgentWebSocketEvents.AgentAudioDone, on_agent_audio_done)
        dg_connection.on(AgentWebSocketEvents.Close, on_close)
        dg_connection.on(AgentWebSocketEvents.Error, on_error)
        dg_connection.on(AgentWebSocketEvents.Unhandled, on_unhandled)

        current_date = datetime.now().strftime("%A, %B %d, %Y")
        instructions = INSTRUCTIONS_PATH.read_text().format(now=current_date)
        # connect to websocket
        # TODO check out settings
        agent = Agent(
            think=Think(
                provider=Provider(
                    type='open_ai'
                ),
                model='gpt-4o-mini',
                instructions=instructions,
                functions=FUNCTION_DEFINITIONS,
            )
        )
        options = SettingsConfigurationOptions(agent=agent)
        # options.agent.think.provider.type = "open_ai"
        # options.agent.think.model = "gpt-4o-mini"
        # options.agent.think.instructions = "You are a helpful AI assistant."

        print("\n\nPress Enter to stop...\n\n")
        # if await dg_connection.start(options, services=uow_services) is False:
        if await dg_connection.start(options) is False:
            print("Failed to start connection")
            return

        # wait until cancelled
        try:
            while True:
                await asyncio.sleep(2)
        except asyncio.CancelledError:
            # This block will be executed when the shutdown coroutine cancels all tasks
            pass
        finally:
            await dg_connection.finish()

        print("Finished")

    except ValueError as e:
        print(f"Invalid value encountered: {e}")
        raise
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        raise
    finally:
        await client.close()


async def shutdown(signal, loop, dg_connection):
    print(f"Received exit signal {signal.name}...")
    await dg_connection.finish()
    tasks = [t for t in asyncio.all_tasks() if t is not asyncio.current_task()]
    [task.cancel() for task in tasks]
    print(f"Cancelling {len(tasks)} outstanding tasks")
    await asyncio.gather(*tasks, return_exceptions=True)
    loop.stop()
    print("Shutdown complete.")

if __name__ == "__main__":
    asyncio.run(main())

