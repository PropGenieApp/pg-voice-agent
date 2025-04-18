import ast
import json
import time
from datetime import datetime, timedelta
from typing import Mapping

from schema.xano import (
    CalendarSlotsRequest,
    CreateAppointmentRequest,
    SearchPropertyResponse,
    TimeSlot,
)
from services.xano import XanoService

from deepgram import (
    FunctionCallRequest,
)

_APPOINTMENT_CREATED_MESSAGE = "Appointment created successfully"
_APPOINTMENT_NOT_CREATED_MESSAGE = "Couldn't create appointment"

class FunctionCallHandler:

    def __init__(self, xano_service: XanoService):
        self.xano_service = xano_service
        self.function_mapping = {
            'searchForProperties': self.search_for_properties,
            'getFreeCalendarSlots': self.get_free_calendar_slots,
            'createAppointment': self.create_appointment,
            'end_call': self.end_call,
        }

    async def search_for_properties(self, params: dict) -> SearchPropertyResponse:
        search_address: str = params.get('search_address')
        properties: SearchPropertyResponse = await self.xano_service.search_property(search_address)
        return properties

    async def get_free_calendar_slots(self, params: dict) -> list[TimeSlot]:
        from_dt = datetime.fromisoformat(params['from_ts'])
        to_dt = from_dt + timedelta(hours=100)
        post_code = params['prop_postcode']
        post_code = post_code.split()[0]
        event_type = params['event_type']
        print('-' * 250)
        print('INCOMING DATA TO FUNCTION "get_free_calendar_slots":')
        print(f'{from_dt =}')
        print(f'{to_dt =}')
        print(f'{post_code =}')
        print(f'{event_type =}')
        print('-' * 250)
        from_ts = int(from_dt.timestamp()) * 1000
        to_ts = int(to_dt.timestamp()) * 1000
        payload = CalendarSlotsRequest(
            from_ts=from_ts,
            to_ts=to_ts,
            prop_postcode=post_code,
            event_type=event_type,
        )
        slots: list[TimeSlot] | None = await self.xano_service.get_calendar_slots(payload)
        return slots

    async def create_appointment(self, params: dict) -> str:
        print('-' * 250)
        print('INCOMING DATA TO FUNCTION "create_appointment":')
        print(json.dumps(params, indent=4, ensure_ascii=False))
        start = datetime.fromisoformat(params['start'])
        end = datetime.fromisoformat(params['end'])
        start_ts = int(start.timestamp()) * 1000
        end_ts = int(end.timestamp()) * 1000
        payload = CreateAppointmentRequest(
            start=start_ts,
            end=end_ts,
            name=params['name'],
            address=params['address'],
            contact=params['contact'],
            agent_id=params['agent_id'],
            event_type=params['event_type'],
            property_id=params['property_id'],
        )
        response = await self.xano_service.create_appointment(payload)
        if response is None:
            return _APPOINTMENT_NOT_CREATED_MESSAGE
        return _APPOINTMENT_CREATED_MESSAGE

    async def end_call(self, params: dict) -> Mapping:
        # TODO It does not work right now
        print("CALLING FUNCTION ENDING THE CALL")
        farewell_type = params.get("farewell_type", "general")
        if farewell_type == "thanks":
            message = "Thank you for calling! Have a great day!"
        elif farewell_type == "help":
            message = "I'm glad I could help! Have a wonderful day!"
        else:  # general
            message = "Goodbye! Have a nice day!"

        # Prepare messages but don't send them
        inject_message = {"type": "InjectAgentMessage", "message": message}

        close_message = {"type": "close"}

        # Return both messages to be sent in correct order by the caller
        return {
            "function_response": {"status": "closing", "message": message},
            "inject_message": inject_message,
            "close_message": close_message,
        }

    async def handle_function_call(self, function_call_request: FunctionCallRequest) -> str:
        """
        Handle function calls with proper error handling and timing.
        
        Args:
            function_call_request: The request containing function name and parameters
            
        Returns:
            dict: The result of the function call
        """
        func_name = function_call_request.function_name
        print('#' * 100)
        print('Func triggered - ', func_name)
        print('#' * 100)

        input_data = function_call_request.input
        if not input_data:
            error_msg = f'The value received is not valid json. Received value - {function_call_request.input}'
            return json.dumps({"error": error_msg}, indent=4, ensure_ascii=False)

        # Parse input data
        try:
            # TODO This is a bug from the deepgram. So I need to find out how to handle it correctly
            valid_dict_data: dict = ast.literal_eval(input_data)
        except (ValueError, SyntaxError) as e:
            return json.dumps({"error": f"Invalid input format: {str(e)}"}, indent=4, ensure_ascii=False)

        # Get the function from our mapping
        func = self.function_mapping.get(func_name)
        if not func:
            error_msg = f"Function {func_name} not found"
            print(error_msg)
            return json.dumps({"error": error_msg}, indent=4, ensure_ascii=False)

        # Execute the function with timing
        try:
            start_time = time.monotonic()
            result = await func(valid_dict_data)
            execution_time = time.monotonic() - start_time
            print(f"Function '{func_name}' execution time: {execution_time:.4f}s")
            
            # Handle the end_call function specially since it has a specific return structure
            if func_name == "end_call" and isinstance(result, dict) and "function_response" in result:
                # The end_call function already returns a formatted object that needs special handling
                return json.dumps(result, indent=4, ensure_ascii=False)
            
            # Standard serialization based on return type
            if isinstance(result, str) and (result.startswith('{') or result.startswith('[')):
                # Result is already a JSON string, return as is
                return result
            elif isinstance(result, (dict, list)):
                # Result is a Python dict or list, serialize to JSON
                return json.dumps(result, indent=4, ensure_ascii=False)
            elif hasattr(result, "model_dump"):
                # Result is a Pydantic model
                return json.dumps(result.model_dump(), indent=4, ensure_ascii=False)
            else:
                # Result is some other type (like a primitive), wrap in a dict
                return json.dumps({"result": result}, indent=4, ensure_ascii=False)
            
        except Exception as e:
            print(f"Error executing function '{func_name}': {str(e)}")
            return json.dumps({"error": str(e)}, indent=4, ensure_ascii=False)


FUNCTION_DEFINITIONS = [
    {
        "name": "searchForProperties",
        "description": """Use this function to search available properties for the client""",
        "parameters": {
            "type": "object",
            "properties": {
                "search_address": {
                    "type": "string",
                    "description": "The address to lookup available properties",
                }
            },
            "required": ["search_address"],
        },
    },

    {
        "name": "getFreeCalendarSlots",
        "description": "Use this function to retrieve free calendar slots based on provided time range and location",
        "parameters": {
            "type": "object",
            "properties": {
                # "to_ts": {
                #     "type": "string",
                #     "description": "The end time of the desired slot range (ISO format). Calculate as start time + 12 hours"
                # },
                "from_ts": {
                    "type": "string",
                    "description": "The start time of the desired slot range (ISO format)"
                },
                "prop_postcode": {
                    "type": "string",
                    "description": "The postcode to check calendar availability"
                },
                "event_type": {
                    "type": "string",
                    "description": "The type of event to check availability for",
                    "enum": ["Valuation", "Viewing"]
                }
            },
            "required": ["from_ts", "prop_postcode", "event_type"]
        }
    },
    {
        "name": "createAppointment",
        "description": "Use this function to create a new appointment for valuation or viewing",
        "parameters": {
            "type": "object",
            "properties": {
                "start": {
                    "type": "string",
                    "description": "Appointment start time (ISO format)"
                },
                "end": {
                    "type": "string",
                    "description": "Appointment end time (ISO format)"
                },
                "name": {
                    "type": "string",
                    "description": "The name of the client"
                },
                "address": {
                    "type": "string",
                    "description": "The appointment address"
                },
                "contact": {
                    "type": "string",
                    "description": "Contact details for the appointment (email or mobile phone)"
                },
                "agent_id": {
                    "type": "string",
                    "description": "ID of the assigned agent"
                },
                "event_type": {
                    "type": "string",
                    "enum": ["Valuation", "Viewing"],
                    "description": "Type of appointment: valuation or viewing"
                },
                "property_id": {
                    "type": "string",
                    "description": "ID of the property involved"
                },
                "additional_information": {
                    "type": "string",
                    "description": "Any extra info about the appointment"
                }
            },
            "required": ["start", "end", "name", "address", "contact", "agent_id", "event_type", "property_id"]
        }
    },
    {
    "name": "end_call",
    "description": """End the conversation and close the connection. Call this function when:
     - User says goodbye, thank you, etc.
     - User indicates they're done ("that's all I need", "I'm all set", etc.)
     - User wants to end the conversation

     Examples of triggers:
     - "Thank you, bye!"
     - "That's all I needed, thanks"
     - "Have a good day"
     - "Goodbye"
     - "I'm done"

     Do not call this function if the user is just saying thanks but continuing the conversation.""",
        "parameters": {
            "type": "object",
            "properties": {
                "farewell_type": {
                    "type": "string",
                    "description": "Type of farewell to use in response",
                    "enum": ["thanks", "general", "help"],
                }
            },
            "required": ["farewell_type"],
        },
    },
]
