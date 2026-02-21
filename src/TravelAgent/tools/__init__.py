"""Travel Agent Tools Package

This module exports all available tools for the travel agent.
"""

from .travel_tool import get_random_destination

from .timeseries_tool import (
    get_weather_forecast,
    get_hotel_prices,
    get_flight_prices,
    get_tourist_volume,
    get_events_calendar,
)

from .search_tool import (
    search_travel_info,
    search_destinations_by_criteria,
)

from .booking_tool import (
    search_hotel_destinations,
    search_hotels,
    get_hotel_prices_live,
    search_flights,
    check_booking_api_status,
)

__all__ = [
    "get_random_destination",
    "get_weather_forecast",
    "get_hotel_prices",
    "get_flight_prices",
    "get_tourist_volume",
    "get_events_calendar",
    "search_travel_info",
    "search_destinations_by_criteria",
    "search_hotel_destinations",
    "search_hotels",
    "get_hotel_prices_live",
    "search_flights",
    "check_booking_api_status",
]
