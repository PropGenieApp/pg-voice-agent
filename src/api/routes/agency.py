#####################################################################################################
from typing import Final

from fastapi import APIRouter, Depends, HTTPException, Response, status
from dependencies.services_deps import get_agency_service
from schema.agency import (
    AgencyCreate,
    AgencyUpdate,
    AgencyOut,
)
from services.agency import AgencyService

#####################################################################################################

router: Final = APIRouter(tags=["Agency"], prefix="/api/agency")

#####################################################################################################

@router.get("/", response_model=list[AgencyOut])
async def get_agency_list(
    agency_service: AgencyService = Depends(get_agency_service),
) -> list[AgencyOut]:
    # TODO: add pagination. Ask frontend what kind of pagination need
    try:
        return await agency_service.get_agency_list()
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to get agency list")

#####################################################################################################

@router.get("/{agency_id}", response_model=AgencyOut)
async def get_agency(
    agency_id: str,
    agency_service: AgencyService = Depends(get_agency_service),
) -> AgencyOut:
    return await agency_service.get_agency(agency_id)


#####################################################################################################


@router.post("/", response_model=AgencyOut)
async def create_agency(
    agency: AgencyCreate,
    agency_service: AgencyService = Depends(get_agency_service),
) -> AgencyOut:
    try:
        return await agency_service.create_agency(agency)
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to create agency")


#####################################################################################################


@router.put("/{agency_id}", response_model=AgencyOut)
async def update_agency(
    agency_id: str,
    payload: AgencyUpdate,
    agency_service: AgencyService = Depends(get_agency_service),
) -> AgencyOut:
    return await agency_service.update_agency(agency_id, payload)


#####################################################################################################


@router.delete("/{agency_id}", status_code=204)
async def delete_agency(
    agency_id: str, agency_service: AgencyService = Depends(get_agency_service)
):
    if not await agency_service.delete_agency(agency_id):
        raise HTTPException(status_code=404, detail="Agency not found")
    return Response(status_code=status.HTTP_204_NO_CONTENT)


#####################################################################################################
