#####################################################################################################

from typing import Literal
from pydantic import BaseModel


#####################################################################################################

class SearchPropertyItem(BaseModel):
    external_id: str
    address: str
    city: str
    country: str
    state: str
    postcode: str
    # property_type: str | None
    # bedroom_count: int | None
    # bathroom_count: int | None
    # floor_count: int | None
    # date_available_for_sale: date | None
    # short_description: str | None
    # long_description: str | None
    # glazing: str | None
    # parking_type: str | None

class SearchPropertyResponse(BaseModel):
    items: list[SearchPropertyItem]

#####################################################################################################

class TimeSlot(BaseModel):
    agent_id: str
    agent_name: str
    start: str
    end: str

class CalendarSlotsRequest(BaseModel):
    from_ts: int
    to_ts: int
    prop_postcode: str
    event_type: Literal['Viewing', 'Valuation']

class CalendarSlotsResponse(BaseModel):
    slots: list[TimeSlot]

#####################################################################################################

class CreateAppointmentRequest(BaseModel):
    start: int
    end: int
    name: str
    address: str
    contact: str
    event_type: Literal['Viewing', 'Valuation']
    property_id: str
    agent_id: str

#####################################################################################################
