from __future__ import annotations

from typing import Any, Dict, List, Optional

import httpx
from genxai.tools.base import Tool, ToolCategory, ToolMetadata, ToolParameter

OPENSKY_API_URL = "https://opensky-network.org/api/states/all"
NOMINATIM_API_URL = "https://nominatim.openstreetmap.org/search"


class FlightStatusSearchTool(Tool):
    def __init__(self) -> None:
        metadata = ToolMetadata(
            name="flight_status_search",
            description=(
                "Lookup real-time flight status using OpenSky data (no pricing). "
                "Returns aircraft in the destination region."
            ),
            category=ToolCategory.CUSTOM,
            tags=["travel", "flights", "status"],
        )
        params = [
            ToolParameter(name="destination", type="string", description="Destination city"),
            ToolParameter(
                name="bbox",
                type="array",
                description=(
                    "Optional bounding box [min_lon, min_lat, max_lon, max_lat] to refine destination area."
                ),
                items={"type": "number", "description": "Bounding box coordinate"},
            ),
        ]
        super().__init__(metadata, params)

    async def _execute(self, **kwargs: Any) -> Any:
        destination = kwargs.get("destination")
        bbox = kwargs.get("bbox")
        params: Dict[str, Any] = {}
        if bbox and len(bbox) == 4:
            params["bbox"] = ",".join(str(value) for value in bbox)

        async with httpx.AsyncClient(timeout=15) as client:
            response = await client.get(OPENSKY_API_URL, params=params)
            response.raise_for_status()
            payload = response.json()

        states = payload.get("states") or []
        options = []
        for entry in states[:10]:
            options.append(
                {
                    "icao24": entry[0],
                    "callsign": (entry[1] or "").strip(),
                    "origin_country": entry[2],
                    "longitude": entry[5],
                    "latitude": entry[6],
                    "altitude": entry[7],
                    "velocity": entry[9],
                }
            )

        return {
            "success": True,
            "destination": destination,
            "source": "OpenSky",
            "options": options,
            "limitations": "OpenSky provides live aircraft positions without fares or availability.",
        }


class HotelPoiSearchTool(Tool):
    def __init__(self) -> None:
        metadata = ToolMetadata(
            name="hotel_poi_search",
            description="Search hotels using OpenStreetMap Nominatim (no pricing).",
            category=ToolCategory.CUSTOM,
            tags=["travel", "hotels"],
        )
        params = [
            ToolParameter(name="destination", type="string", description="Destination city"),
            ToolParameter(
                name="limit",
                type="number",
                description="Maximum number of hotel results",
            ),
        ]
        super().__init__(metadata, params)

    async def _execute(self, **kwargs: Any) -> Any:
        destination = kwargs.get("destination")
        limit = int(kwargs.get("limit") or 8)
        params = {
            "q": f"hotel {destination}",
            "format": "json",
            "limit": limit,
        }
        headers = {"User-Agent": "GenXAI-Travel-Agent"}
        async with httpx.AsyncClient(timeout=15) as client:
            response = await client.get(NOMINATIM_API_URL, params=params, headers=headers)
            response.raise_for_status()
            payload = response.json()

        options = [
            {
                "name": item.get("display_name"),
                "latitude": item.get("lat"),
                "longitude": item.get("lon"),
                "category": item.get("type"),
            }
            for item in payload
        ]

        return {
            "success": True,
            "destination": destination,
            "source": "OpenStreetMap",
            "options": options,
            "limitations": "OSM data does not include pricing or live availability.",
        }


class ActivityPoiSearchTool(Tool):
    def __init__(self) -> None:
        metadata = ToolMetadata(
            name="activity_poi_search",
            description="Suggest activities using OpenStreetMap POI search.",
            category=ToolCategory.CUSTOM,
            tags=["travel", "activities"],
        )
        params = [
            ToolParameter(name="destination", type="string", description="Destination city"),
            ToolParameter(
                name="interests",
                type="array",
                description="Traveler interests",
                items={"type": "string", "description": "Interest category"},
            ),
            ToolParameter(
                name="limit",
                type="number",
                description="Maximum number of activity results",
            ),
        ]
        super().__init__(metadata, params)

    async def _execute(self, **kwargs: Any) -> Any:
        destination = kwargs.get("destination")
        interests = kwargs.get("interests") or ["attractions", "museum", "park"]
        limit = int(kwargs.get("limit") or 8)
        query = f"{' '.join(interests)} {destination}"
        params = {
            "q": query,
            "format": "json",
            "limit": limit,
        }
        headers = {"User-Agent": "GenXAI-Travel-Agent"}
        async with httpx.AsyncClient(timeout=15) as client:
            response = await client.get(NOMINATIM_API_URL, params=params, headers=headers)
            response.raise_for_status()
            payload = response.json()

        options = [
            {
                "name": item.get("display_name"),
                "latitude": item.get("lat"),
                "longitude": item.get("lon"),
                "category": item.get("type"),
            }
            for item in payload
        ]

        return {
            "success": True,
            "destination": destination,
            "source": "OpenStreetMap",
            "interests": interests,
            "options": options,
            "limitations": "OSM data does not include ticket pricing or reservations.",
        }


def register_real_travel_tools() -> None:
    from genxai.tools.registry import ToolRegistry

    for tool in [FlightStatusSearchTool(), HotelPoiSearchTool(), ActivityPoiSearchTool()]:
        if not ToolRegistry.get(tool.metadata.name):
            ToolRegistry.register(tool)