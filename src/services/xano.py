#####################################################################################################

from http import HTTPStatus
from typing import Final
from logging import Logger
from aiohttp import ClientSession

from schema.xano import CalendarSlotsRequest, CreateAppointmentRequest, SearchPropertyResponse, \
    TimeSlot
from services.base import BaseService
from configs.settings import AppSettings

#####################################################################################################

class XanoService(BaseService):
    # TODO handle bad response statuses

    def __init__(
        self,
        app_settings: AppSettings,
        aiohttp_client: ClientSession,
        logger: Logger,
    ) -> None:
        self._logger = logger
        self._aiohttp_client: Final = aiohttp_client
        self._headers = {
            'Authorization': f'Bearer {app_settings.xano_dev_api_token}'
        }
        self._xano_api_url: Final = 'https://xgpn-deh3-dvvh.n7c.xano.io/api:7-FXIT0K'  # FIXME to env?
        self._calendar_slots_url: Final = f'{self._xano_api_url}/calendar_slots'
        self._search_property_url: Final = f'{self._xano_api_url}/property_search_address'
        self._create_appointment_url: Final = f'{self._xano_api_url}/calendar'

    async def get_calendar_slots(
        self,
        payload: CalendarSlotsRequest,
    ) -> list[TimeSlot] | None:
        response = await self._aiohttp_client.post(
            json=payload.model_dump(),
            url=self._calendar_slots_url,
            headers=self._headers,
        )
        if response.status != HTTPStatus.OK:
            self._logger.error(f'Failed to get calendar slots: {response.status}')
            return
        calendar_slots_json = await response.json()
        return [TimeSlot(**slot) for slot in calendar_slots_json]

    async def create_appointment(
        self,
        payload: CreateAppointmentRequest,
    ) -> bool:
        response = await self._aiohttp_client.post(
            json=payload.model_dump(),
            url=self._create_appointment_url,
            headers=self._headers,
        )
        if response.status != HTTPStatus.OK:
            self._logger.error(f'Failed to create appointment: {response.status}')
            return False
        return True

    async def search_property(self, search_address: str) -> SearchPropertyResponse | None:
        response = await self._aiohttp_client.post(
            json=dict(search_address=search_address),
            url=self._search_property_url,
            headers=self._headers,
        )
        if response.status != HTTPStatus.OK:
            self._logger.error(f'Failed to search property: {response.status}')
            return None
        properties_json = await response.json()
        return SearchPropertyResponse(**properties_json)

#####################################################################################################

