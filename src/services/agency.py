# TODO: ADD REPOSITORY CLASS FOR AGENCY
# TODO: add validations and exceptions when create / update agency
# TODO: Consider the possibility of creating a template of instructions directly on
#  the client side based on the selected tasks
#####################################################################################################

from typing import Final

from fastapi import HTTPException
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from schema.agency import (
    Agency,
    AgencyCreate,
    AgencySettings,
    AgencyUpdate,
    AudioSettings,
    DeepgramAgentSettings, 
    Function,
    InputSettings,
    OutputSettings,
    ThinkProvider,
    ThinkSettings,
    AgencyOut,
    )
from services.base import BaseService
from db.models.agency import Agency as AgencyModel
from services.func_tools import FUNCTION_DEFINITIONS
from utils.prompt import PromptTemplateBuilder

#####################################################################################################

class AgencyService(BaseService):
    _DEFAULT_AUDIO_SETTINGS: Final = AudioSettings(
        input=InputSettings(),
        output=OutputSettings(),
    )
    _DEFAULT_THINK_MODEL: Final = 'gpt-4o-mini'

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    def _create_instructions(self, view_task: bool, valuation_task: bool) -> str:
        tasks = []
        if view_task:
            tasks.append('viewing')
        if valuation_task:
            tasks.append('valuation')
        prompt_template_builder = PromptTemplateBuilder()
        return prompt_template_builder.build_instructions(tasks=tasks)

    def _create_functions(self, view_task: bool, valuation_task: bool) -> list[Function]:
        # FIXME
        return [Function.model_validate(func) for func in FUNCTION_DEFINITIONS]

    def _create_think_settings(
        self,
        view_task: bool,
        valuation_task: bool
    ) -> ThinkSettings:
        instructions = self._create_instructions(view_task, valuation_task)
        functions = self._create_functions(view_task, valuation_task)
        return ThinkSettings(
            provider=ThinkProvider(
                type="openai",
            ),
            model=self._DEFAULT_THINK_MODEL,
            instructions=instructions,
            functions=functions,
        )

    async def get_agency_list(self, limit: int = 10, offset: int = 0) -> list[AgencyOut]:
        stmt = select(AgencyModel).offset(offset).limit(limit)
        agencies = await self._session.execute(stmt)
        return [AgencyOut.model_validate(agency, from_attributes=True) for agency in agencies]

    async def create_agency(self, agency: AgencyCreate) -> AgencyOut:
        deepgram_agent_settings = DeepgramAgentSettings(
            think=self._create_think_settings(
                view_task=agency.viewing_task,
                valuation_task=agency.valuation_task
            ),
            speak=agency.settings.agent.speak,
            listen=agency.settings.agent.listen,
        )
        advanced_settings = AgencySettings(
            audio=self._DEFAULT_AUDIO_SETTINGS,
            agent=deepgram_agent_settings,
        )

        agency_schema = Agency(
            id=agency.id,
            assistant_name=agency.assistant_name,
            agency_name=agency.agency_name,
            agency_location=agency.agency_location,
            agency_timezone=agency.agency_timezone,
            agency_description=agency.agency_description,
            settings=advanced_settings,
        )
        agency_db = AgencyModel(**agency_schema.model_dump())
        self._session.add(agency_db)
        await self._session.commit()
        return AgencyOut.model_validate(agency_schema, from_attributes=True)
    
    async def update_agency(self, agency_id: str, agency: AgencyUpdate) -> AgencyOut:
        raise NotImplementedError("Not implemented yet")

    async def get_agency(self, agency_id: str) -> AgencyOut:
        stmt = select(AgencyModel).where(AgencyModel.id == agency_id)
        agency_db = await self._session.execute(stmt)
        agency_db = agency_db.scalar_one_or_none()
        if not agency_db:
            raise HTTPException(status_code=404, detail="Agency not found")
        return AgencyOut.model_validate(agency_db, from_attributes=True)

    async def delete_agency(self, agency_id: str) -> bool:
        stmt = delete(AgencyModel).where(AgencyModel.id == agency_id)
        await self._session.execute(stmt)
        res = await self._session.commit()
        return res.rowcount > 0

#####################################################################################################
