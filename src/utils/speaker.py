import asyncio
import tempfile
import os
import subprocess
import logging
from threading import Thread

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class WebmOpusPlayer:
    def __init__(self):
        self.process = None
        self.is_playing = False
        self.fifo_path = None
        self.writer_thread = None
        self.data_queue = asyncio.Queue()

    def create_player(self):
        """Create a FIFO and start ffplay process"""
        # Create a named pipe (FIFO)
        fd, temp_path = tempfile.mkstemp(suffix='.fifo')
        os.close(fd)
        os.unlink(temp_path)  # Remove the regular file
        self.fifo_path = temp_path
        os.mkfifo(self.fifo_path)

        logger.info(f"Created FIFO at {self.fifo_path}")

        # Start FFplay process
        cmd = [
            'ffplay',
            '-i', self.fifo_path,
            '-nodisp',
            '-autoexit',
            '-loglevel', 'warning',
            '-af', 'volume=1.0'
        ]

        logger.info(f"Starting ffplay with command: {' '.join(cmd)}")

        try:
            self.process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            logger.info("FFplay process started")

            # Start a thread to check if ffplay exits
            def monitor_process():
                self.process.wait()
                logger.info("FFplay process exited")
                self.is_playing = False

            monitor_thread = Thread(target=monitor_process)
            monitor_thread.daemon = True
            monitor_thread.start()

            self.is_playing = True
            return True
        except Exception as e:
            logger.error(f"Error starting ffplay: {e}")
            self.cleanup()
            return False

    def start_writer_thread(self):
        """Start a thread that writes data from the queue to the FIFO"""
        self.writer_thread = Thread(target=self._writer_thread_func)
        self.writer_thread.daemon = True
        self.writer_thread.start()

    def _writer_thread_func(self):
        """Thread function that writes data from the queue to the FIFO"""
        try:
            # Open the FIFO for writing (blocking until ffplay opens it for reading)
            logger.info(f"Opening FIFO for writing: {self.fifo_path}")
            with open(self.fifo_path, 'wb') as fifo:
                logger.info("FIFO opened for writing")

                # Write WebM header if needed (you may need to modify this based on your data)
                # fifo.write(webm_header)

                while self.is_playing:
                    try:
                        # Get data from the queue with a timeout
                        data = asyncio.run_coroutine_threadsafe(
                            self.data_queue.get(), asyncio.get_event_loop()
                        ).result(timeout=1.0)

                        if data is None:  # None is our signal to stop
                            logger.info("Received stop signal in writer thread")
                            break

                        # Write the data to the FIFO
                        fifo.write(data)
                        fifo.flush()
                    except asyncio.TimeoutError:
                        continue  # No data available, try again
                    except Exception as e:
                        logger.error(f"Error in writer thread: {e}")
                        break

                logger.info("Writer thread exiting")
        except Exception as e:
            logger.error(f"Error opening or writing to FIFO: {e}")
        finally:
            self.is_playing = False

    async def feed_data(self, data):
        """Feed audio data to the player queue"""
        if self.is_playing:
            await self.data_queue.put(data)
            return True
        return False

    def cleanup(self):
        """Clean up resources"""
        self.is_playing = False

        # Signal the writer thread to stop
        if self.writer_thread and self.writer_thread.is_alive():
            asyncio.run_coroutine_threadsafe(
                self.data_queue.put(None), asyncio.get_event_loop()
            )

        # Terminate ffplay process
        if self.process:
            try:
                self.process.terminate()
                try:
                    self.process.wait(timeout=2)
                except subprocess.TimeoutExpired:
                    self.process.kill()
                self.process = None
                logger.info("FFplay process terminated")
            except Exception as e:
                logger.error(f"Error terminating ffplay: {e}")

        # Remove the FIFO
        if self.fifo_path and os.path.exists(self.fifo_path):
            try:
                os.unlink(self.fifo_path)
                logger.info(f"Removed FIFO: {self.fifo_path}")
            except Exception as e:
                logger.error(f"Error removing FIFO: {e}")
            self.fifo_path = None
