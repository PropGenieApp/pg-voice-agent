#####################################################################################################

from contextlib import asynccontextmanager
from logging import Logger
from typing import Any, Callable, Final, Sequence

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncEngine, async_sessionmaker

from configs.settings import AppSettings
from db.connection.session import DatabaseManager
from services.xano import XanoService
from utils.aiohttp_utils import create_aiohttp_client

#####################################################################################################

class App(FastAPI):
    def __init__(
        self,
        logger: Logger,
        app_settings: AppSettings,
        db_engine: AsyncEngine,
        db_session_maker: async_sessionmaker,
        on_startup: Sequence[Callable[[], Any]] | None = None,
        on_shutdown: Sequence[Callable[[], Any]] | None = None,
    ) -> None:
        self.app_settings: Final = app_settings
        self.db_manager = DatabaseManager(db_engine, db_session_maker)
        self.logger: Final = logger

        super().__init__(
            debug=app_settings.dev_mode,
            title=app_settings.app_name,
            version=app_settings.app_version,
            lifespan=lifespan,
            on_startup=on_startup,
            on_shutdown=on_shutdown,
        )

        self.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        self.aiohttp_client: Final = create_aiohttp_client()
        self.xano_service = XanoService(app_settings, self.aiohttp_client, logger)

        # TODO: mount only if dev_mode is True
        self.mount("/static", StaticFiles(directory="static"), name="static")

        self.templates = Jinja2Templates(directory="templates")

#####################################################################################################

@asynccontextmanager
async def lifespan(app: App):

    yield
    # Cleanup on shutdown
    await app.db_manager.close()
    await app.aiohttp_client.close()
