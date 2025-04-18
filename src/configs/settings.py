import json
from typing import Final, Mapping, Any

from pydantic_settings import BaseSettings, SettingsConfigDict


class AppSettings(BaseSettings):
    model_config = SettingsConfigDict(
        case_sensitive=False,
    )
    app_name: str = "PG Voice Agent"
    app_version: str = '1.0'

    dev_mode: bool

    app_host: str = "0.0.0.0"
    app_port: int = 5000

    postgres_user: str
    postgres_password: str
    postgres_host: str
    postgres_port: int
    postgres_db: str

    xano_dev_api_token: str

    def __str__(self, /) -> str:
        obj_for_output: Final = self._get_fields_for_output()
        return f'APP INFO: {json.dumps(obj_for_output, indent=4, ensure_ascii=False)}'

    #####################################################################################################

    def _get_fields_for_output(self) -> Mapping[str, Any]:
        obj_for_output: Final = {
            'APP_NAME': self.app_name,
            'APP_VERSION': self.app_version,
            'SERVER_PORT': self.app_port,
            'SERVER_EXTERNAL_URL': self.app_host,
            'DEV_MODE': self.dev_mode,
            'POSTGRES_PORT': self.postgres_port,
        }

        return obj_for_output

    @property
    def postgres_async_dsn(self) -> str:
        return (
            f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}@"
            f"{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )
