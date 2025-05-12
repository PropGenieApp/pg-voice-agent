import asyncio
from abc import ABC

from deepgram import AsyncAgentWebSocketClient
from deepgram.clients.common import AbstractAsyncWebSocketClient


class BaseDeepgramClient(AbstractAsyncWebSocketClient, ABC):

    async def finish(self) -> bool:
        """
        Closes the WebSocket connection gracefully.
        """
        self._logger.debug("AbstractAsyncWebSocketClient.finish ENTER")

        try:
            # Signal exit first
            await self._signal_exit()

            # Cancel listen thread with timeout
            if self._listen_thread is not None and not self._listen_thread.done():
                self._listen_thread.cancel()
                try:
                    await asyncio.wait_for(self._listen_thread, timeout=1.0)
                except asyncio.TimeoutError:
                    self._logger.error("Listen thread cancellation timed out")
                except asyncio.CancelledError:
                    self._logger.debug("Listen thread responded to cancellation")
            return True

        except Exception as e:
            self._logger.error(f"Error during finish: {str(e)}")
            return False
        finally:
            self._logger.debug("AbstractAsyncWebSocketClient.finish LEAVE")


class RedefinedAsyncDeepgramAgentClient(AsyncAgentWebSocketClient):
    async def finish(self) -> bool:
        self._logger.debug("AbstractAsyncWebSocketClient.finish ENTER")

        try:
            # Signal exit first
            await self._signal_exit()

            # Redefined parent finish method.
            # Cancel listen thread with timeout
            if self._listen_thread is not None and not self._listen_thread.done():
                self._listen_thread.cancel()
                try:
                    await asyncio.wait_for(self._listen_thread, timeout=1.0)
                except asyncio.TimeoutError:
                    self._logger.error("Listen thread cancellation timed out")
                except asyncio.CancelledError:
                    self._logger.debug("Listen thread responded to cancellation")

            if self._microphone is not None and self._microphone_created:
                self._microphone.finish()
                self._microphone_created = False

            if self._speaker is not None and self._speaker_created:
                self._speaker.finish()
                self._speaker_created = False

            # TODO Исправить реализацию SDK через gather. Тут запускается только одна Task
            tasks = []
            if self._keep_alive_thread is not None:
                self._keep_alive_thread.cancel()
                tasks.append(self._keep_alive_thread)
                self._logger.notice("processing _keep_alive_thread cancel...")
            await asyncio.wait_for(asyncio.gather(*tasks), timeout=10)
            self._logger.notice("threads joined")

            self._speaker = None
            self._microphone = None

        except asyncio.CancelledError as e:
            self._logger.error("tasks cancelled error: %s", e)
            self._logger.debug("AsyncAgentWebSocketClient.finish LEAVE")
            return False

        except asyncio.TimeoutError as e:
            self._logger.error("tasks cancellation timed out: %s", e)
            self._logger.debug("AsyncAgentWebSocketClient.finish LEAVE")
            return False

        except Exception as e:
            self._logger.error(f"Error during finish: {str(e)}")
            return False
