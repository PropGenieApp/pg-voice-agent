import ast

import json
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from logging import Logger
from typing import Any, Final

from deepgram.clients.agent.v1 import FunctionCallRequest
from fastapi import WebSocket

from deepgram import AsyncAgentWebSocketClient, FunctionCallResponse
from pydantic import BaseModel

from schema.conversation import ConversationState
from schema.lead import LeadInfo
from schema.xano import CalendarSlotsRequest, CalendarSlotsResponse, CreateAppointmentRequest, SearchPropertyAgentFormat, SearchPropertyItemAgentFormat, SearchPropertyResponse, TimeSlot
from services.xano import XanoService


class FunctionCommand(ABC):

    def __init__(
        self,
        xano_service: XanoService,
        logger: Logger,
        client_ws: WebSocket,
        deepgram_agent: AsyncAgentWebSocketClient,
        conv_state: ConversationState,
        dev_mode: bool = False,
    ):
        self._xano_service = xano_service
        self._logger = logger
        self._client_ws = client_ws
        self._deepgram_agent = deepgram_agent
        self._dev_mode = dev_mode
        self._conv_state = conv_state

    async def execute(self, function_call_request: FunctionCallRequest) -> None:
        """Common execution logic for all Commands."""
        self._logger.debug(f'Incoming function call request to {self.__class__.__name__}:')
        self._logger.debug(function_call_request.to_json(ensure_ascii=False, indent=4))
        self._conv_state.tool_calls.add(function_call_request.function_name)
        input_data = function_call_request.input
        try:
            serialized_input = self.serialize_input(input_data)
            result = await self._execute(serialized_input)
        except Exception as ex:
            # Return error message even if exception occurred while executing the function
            self._logger.error(f'Error executing function call {function_call_request.function_name}: {ex}')
            result = f"Error executing function call {function_call_request.function_name}: {ex}"
        formatted_response = self.format_response(result, function_call_request.function_call_id)
        await self._deepgram_agent.send(formatted_response.to_json(ensure_ascii=False, indent=4))
        if self._dev_mode:
            await self._client_ws.send_text(formatted_response.to_json(ensure_ascii=False, indent=4))

    @abstractmethod
    async def _execute(self, params: dict[str, Any]) -> Any:
        pass

    @staticmethod
    def serialize_input(input_data: str) -> dict:
        # TODO REFACTOR IT
        serialized_data = ast.literal_eval(input_data)
        if isinstance(serialized_data, dict):
            return serialized_data
        raise ValueError("Input data is not a dictionary")

    @staticmethod
    def format_response(data: Any, func_id: str) -> FunctionCallResponse:
        """
        Format the response to the FunctionCallResponse valid format
        """
        if isinstance(data, BaseModel) and hasattr(data, 'model_dump_json'):
            output = data.model_dump_json(indent=4)
        elif isinstance(data, str) and (data.startswith('{') or data.startswith('[')):
            output = data
        elif isinstance(data, (dict, list)):
            output = json.dumps(data, indent=4, ensure_ascii=False)
        else:
            output = json.dumps({"result": data}, indent=4, ensure_ascii=False)

        return FunctionCallResponse(
            type='FunctionCallResponse',
            function_call_id=func_id,
            output=output,
        )


class CreateAppointmentCommand(FunctionCommand):

    _APPOINTMENT_CREATED_MESSAGE = "Appointment created successfully"
    _APPOINTMENT_NOT_CREATED_MESSAGE = "Couldn't create appointment"

    async def _execute(self, params: dict[str, Any]) -> Any:
        start = datetime.fromisoformat(params['start'])
        end = datetime.fromisoformat(params['end'])
        start_ts = int(start.timestamp()) * 1000
        end_ts = int(end.timestamp()) * 1000
        if not (params.get('email') or params.get('phone')):
            raise ValueError("At least one of email or phone must be provided")
        try:
            payload = CreateAppointmentRequest(
                start=start_ts,
                end=end_ts,
                name=params['name'],
                address=params['address'],
                email=params['email'],
                phone=params['phone'],
                agent_id=params['agent_id'],
                event_type=params['event_type'],
                property_id=params['property_id'],
            )
        except Exception as ex:
            self._logger.error('Invalid payload for creating appointment', exc_info=ex)
            raise ValueError(f'Invalid payload for creating appointment: {ex}')
        response = await self._xano_service.create_appointment(payload)
        if not response:
            return self._APPOINTMENT_NOT_CREATED_MESSAGE
        self._conv_state.lead_created = True
        self._conv_state.lead_info = LeadInfo(
            name=params['name'],
            email=params['email'],
            phone=params['phone'],
        )
        return self._APPOINTMENT_CREATED_MESSAGE


class SearchPropertiesCommand(FunctionCommand):
    
    async def _execute(self, params: dict) -> SearchPropertyAgentFormat:
        search_address: str = params.get('search_address')
        properties: SearchPropertyResponse | None = await self._xano_service.search_property(search_address)
        if not properties:
            return SearchPropertyAgentFormat(items=[])
        
        properties_output = SearchPropertyAgentFormat(
            items=[SearchPropertyItemAgentFormat(
                property_id=p.external_id,
                address=p.address,
                city=p.city,
                country=p.country,
                state=p.state,
                postcode=p.postcode,
            ) for p in properties.items]
        )
        return properties_output
    

class GetFreeCalendarSlotsCommand(FunctionCommand):

    _MAX_NUMBER_OF_SLOTS_RESPONSE: Final[int] = 10

    async def _execute(self, params: dict) -> CalendarSlotsResponse:
        from_dt = datetime.fromisoformat(params['from_ts'])
        to_dt = from_dt + timedelta(hours=50)
        post_code = params['prop_postcode']
        post_code = post_code.split()[0]
        event_type = params['event_type']
        from_ts = int(from_dt.timestamp()) * 1000
        to_ts = int(to_dt.timestamp()) * 1000
        
        payload = CalendarSlotsRequest(
            from_ts=from_ts,
            to_ts=to_ts,
            prop_postcode=post_code,
            event_type=event_type,
        )
        slots: list[TimeSlot] | None = await self._xano_service.get_calendar_slots(payload)
        self._conv_state.set_purpose_by_event_type(event_type)
        if not slots:
            return CalendarSlotsResponse(slots=[])
        return CalendarSlotsResponse(slots=slots[:self._MAX_NUMBER_OF_SLOTS_RESPONSE])
    

class EndCallCommand(FunctionCommand):
    def __init__(self, exit_callback, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._exit_callback = exit_callback

    async def execute(self, function_call_request: FunctionCallRequest) -> Any:
        self._logger.debug(f'Incoming function call request to {self.__class__.__name__}:')
        self._logger.debug(function_call_request.to_json(ensure_ascii=False, indent=4))
        input_data = function_call_request.input
        try:
            serialized_input = self.serialize_input(input_data)
            result = await self._execute(serialized_input)
        except Exception as ex:
            # Return error message even if exception occurred while executing the function
            self._logger.error(f'Error executing function call {function_call_request.function_name}: {ex}')
            result = f"Error executing function call {function_call_request.function_name}: {ex}"
        function_response = result["function_response"]
        inject_message = result["inject_message"]
        formatted_response = self.format_response(function_response, function_call_request.function_call_id)
        await self._deepgram_agent.send(formatted_response.to_json())
        await self._deepgram_agent.send(json.dumps(inject_message))
        # TODO work with the implementation of exit_callback. It should voice last inject message from agent
        await self._exit_callback()

    async def _execute(self, params: dict) -> dict:
        farewell_type = params.get("farewell_type", "general")
        
        if farewell_type == "thanks":
            message = "Thank you for calling! Have a great day!"
        elif farewell_type == "help":
            message = "I'm glad I could help! Have a wonderful day!"
        else:  # general
            message = "Goodbye! Have a nice day!"

        inject_message = {"type": "InjectAgentMessage", "message": message}

        close_message = {"type": "close"}
        
        # Return the response structure
        return {
            "function_response": {"status": "closing", "message": message},
            "inject_message": inject_message,
            "close_message": close_message,
        }
    