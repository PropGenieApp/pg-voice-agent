import asyncio
from typing import Final

import uvicorn
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from api.routes import setup_routes
from app import App
from configs.logger import setup_logging
from configs.settings import AppSettings

#####################################################################################################

LOGGER: Final = setup_logging()

#####################################################################################################

async def run_server() -> None:
    LOGGER.info("Start running application...")
    load_dotenv()
    app_settings = AppSettings()
    LOGGER.info(app_settings)
    # db_engine = create_async_engine(url=app_settings.postgres_async_dsn, echo=app_settings.dev_mode)
    db_engine = create_async_engine(url=app_settings.postgres_async_dsn, echo=False)
    session_maker = async_sessionmaker(
            db_engine, class_=AsyncSession, expire_on_commit=False, autoflush=False
        )

    app: Final = App(
        logger=LOGGER,
        app_settings=app_settings,
        db_engine=db_engine,
        db_session_maker=session_maker,
    )
    setup_routes(app)
    config = uvicorn.Config(
        app=app,
        host=app_settings.app_host,
        port=app_settings.app_port,
        log_level=LOGGER.level,
        use_colors=True,
        timeout_keep_alive=5,
    )
    server = uvicorn.Server(config)
    await server.serve()

#####################################################################################################

if __name__ == "__main__":
    asyncio.run(run_server())
