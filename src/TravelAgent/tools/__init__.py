"""Travel Agent Tools Package

This module exports all available tools for the travel agent.
"""

# Travel tools
from .travel_tool import get_random_destination

# Time series data tools
from .timeseries_tool import (
    get_weather_forecast,
    get_hotel_prices,
    get_flight_prices,
    get_tourist_volume,
    get_events_calendar,
)

# Search tools
from .search_tool import (
    search_travel_info,
    search_destinations_by_criteria,
)

# Booking.com API tools (real-time data)
from .booking_tool import (
    search_hotel_destinations,
    search_hotels,
    get_hotel_prices_live,
    search_flights,
    check_booking_api_status,
)

__all__ = [
    # Travel
    "get_random_destination",
    # Time series
    "get_weather_forecast",
    "get_hotel_prices",
    "get_flight_prices",
    "get_tourist_volume",
    "get_events_calendar",
    # Search
    "search_travel_info",
    "search_destinations_by_criteria",
    # Booking.com (real-time)
    "search_hotel_destinations",
    "search_hotels",
    "get_hotel_prices_live",
    "search_flights",
    "check_booking_api_status",
]
