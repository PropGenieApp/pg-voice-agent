from typing import Final

FUNCTION_DEFINITIONS: Final = [
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
                "email": {
                    "type": ["string", "null"],
                    "description": "Contact email"
                },
                "phone": {
                    "type": ["string", "null"],
                    "description": "Contact mobile phone"
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
            "required": ["start", "end", "name", "address", "agent_id", "event_type", "property_id", "email", "phone"],
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
