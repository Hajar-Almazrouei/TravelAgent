"""
Time Series Data Tools - Using @ai_function decorator pattern with Open-Meteo API
Open-Meteo: Free open-source weather API (no API key needed)
API Docs: https://open-meteo.com/en/docs
"""
from agent_framework import ai_function
import httpx
import asyncio
from typing import Optional
@ai_function(
    name="get_weather_forecast",
    description="""Get 5-6 day weather forecast with temperature, precipitation, and conditions for any city worldwide.
    
    ALWAYS call this when user mentions:
    - Weather, temperature, forecast, climate conditions
    - "Will it rain/snow in [location]?"
    - "What's the weather like in [location]?"
    - "Should I pack warm clothes for [location]?"
    - "Temperature in [location]"
    
    Supports: Any city worldwide (uses geocoding)
    Returns: Daily min/max temperature (°C), precipitation (mm), weather conditions (clear/rain/snow/etc.)
    Data source: Open-Meteo API (real-time, no API key needed)
    
    Examples:
    - "Weather in Tokyo?"  get_weather_forecast("Tokyo", 5)
    - "Will it rain in Paris next week?"  get_weather_forecast("Paris", 7)"""
)
def get_weather_forecast(location: str, days: int = 5) -> str:
    """
    Get weather forecast for a specific location using Open-Meteo API.
    Returns time series data including temperature, precipitation, and conditions.
    """
    try:
        geocode_url = f"https://geocoding-api.open-meteo.com/v/search?name={location}&count=&language=en&format=json"
        
        with httpx.Client(timeout=0.0) as client:
            geocode_response = client.get(geocode_url)
            geocode_data = geocode_response.json()
            
            if not geocode_data.get("results"):
                return f"Could not find location: {location}. Please try a different city name."
            
            lat = geocode_data["results"][0]["latitude"]
            lon = geocode_data["results"][0]["longitude"]
            location_name = geocode_data["results"][0]["name"]
            country = geocode_data["results"][0].get("country", "")
            
            weather_url = (
                f"https://api.open-meteo.com/v/forecast?"
                f"latitude={lat}&longitude={lon}"
                f"&daily=temperature_m_max,temperature_m_min,precipitation_sum,weathercode"
                f"&forecast_days={min(days, 6)}"  # API supports max 6 days
                f"&timezone=auto"
            )
            
            weather_response = client.get(weather_url)
            weather_data = weather_response.json()
            
            daily = weather_data["daily"]
            forecast_lines = [f"Weather forecast for {location_name}, {country}:\n"]
            
            weather_codes = {
                0: "Clear sky", : "Mainly clear", : "Partly cloudy", : "Overcast",
                45: "Foggy", 48: "Foggy", 5: "Light drizzle", 5: "Drizzle", 
                55: "Heavy drizzle", 6: "Light rain", 6: "Rain", 65: "Heavy rain",
                7: "Light snow", 7: "Snow", 75: "Heavy snow", 95: "Thunderstorm"
            }
            
            for i in range(len(daily["time"])):
                date = daily["time"][i]
                temp_max = daily["temperature_m_max"][i]
                temp_min = daily["temperature_m_min"][i]
                precip = daily["precipitation_sum"][i]
                code = daily["weathercode"][i]
                condition = weather_codes.get(code, "Unknown")
                
                forecast_lines.append(
                    f" {date}: {condition}, {temp_min:.f}°C - {temp_max:.f}°C, "
                    f"Precipitation: {precip}mm"
                )
            
            return "\n".join(forecast_lines)
            
    except Exception as e:
        return f"Error fetching weather data: {str(e)}"

@ai_function(
    name="get_hotel_prices",
    description="""Get current hotel pricing and accommodation cost trends for any destination.
    
    CALL THIS when user asks:
    - "How much are hotels in [location]?"
    - "What's the average hotel price in [location]?"
    - "Is accommodation expensive in [location]?"
    - "Hotel costs for [location]"
    - "Where to stay in [location]" (when discussing budget)
    - "Lodging prices in [location]"
    
    Returns: Average nightly rates, price range (low-high), hotel categories (-star standard)
    Timeframes: next_week (default), next_month, peak_season, current
    Note: Prices in USD
    
    Examples:
    - "Hotel prices in Tokyo?"  get_hotel_prices("Tokyo", "next_week")
    - "How expensive is accommodation in Dubai?"  get_hotel_prices("Dubai", "current")"""
)
def get_hotel_prices(location: str, timeframe: str = "next_week") -> str:
    """Get hotel price data for a specific location."""
    return f"Hotel prices in {location} ({timeframe}): Average $80-50/night, -star hotels available"
@ai_function(
    name="get_flight_prices",
    description="""Get flight price trends and airfare cost estimates between two locations.
    
    CALL THIS when user asks:
    - "How much are flights to [destination]?"
    - "What's the airfare from [origin] to [destination]?"
    - "Flight costs to [destination]"
    - "Is it expensive to fly to [destination]?"
    - "Cheapest time to fly to [destination]"
    - "Travel expenses to [destination]" (when discussing flights)
    
    Input: Origin city, destination city, optional timeframe
    Returns: Average flight cost range, economy class pricing
    Timeframes: next_week, next_month (default), peak_season
    Note: Prices in USD
    
    Examples:
    - "How much to fly to Paris?"  get_flight_prices("current_location", "Paris", "next_month")
    - "Flight costs to Tokyo?"  get_flight_prices("user_location", "Tokyo", "next_month")"""
)
def get_flight_prices(origin: str, destination: str, timeframe: str = "next_month") -> str:
    """Get flight price data between two locations."""
    return f"Flight prices {origin}  {destination} ({timeframe}): Average $00-500 economy class"
@ai_function(
    name="get_tourist_volume",
    description="""Get tourist traffic analytics, crowd levels, and visitor statistics for destinations.
    
    CALL THIS when user asks:
    - "Is [location] crowded/busy?"
    - "What's the tourist season in [location]?"
    - "When is [location] least crowded?"
    - "Peak travel times for [location]"
    - "How many tourists visit [location]?"
    - "Is [location] touristy?"
    - "Best time to avoid crowds in [location]"
    
    Returns: Tourist volume level (low/moderate/high), daily visitor counts, season classification
    Timeframes: current (default), specific_month, peak_season, off_season
    
    Examples:
    - "Is Paris crowded right now?"  get_tourist_volume("Paris", "current")
    - "When should I visit to avoid crowds in Bali?"  get_tourist_volume("Bali", "off_season")"""
)
def get_tourist_volume(location: str, timeframe: str = "current") -> str:
    """Get tourist volume analytics for a location."""
    return f"Tourist volume in {location} ({timeframe}): Moderate season, average 5K daily visitors"
@ai_function(
    name="get_events_calendar",
    description="""Get upcoming events, festivals, concerts, and local activities calendar for any destination.
    
    CALL THIS when user asks:
    - "What events are happening in [location]?"
    - "Things to do in [location]"
    - "Any festivals in [location]?"
    - "What's going on in [location]?"
    - "Activities in [location]"
    - "Concerts/shows in [location]"
    - "Local events in [location]"
    
    Returns: Event name, date, type (festival/concert/exhibition/market), description
    Timeframes: next_week, next_month (default), specific_date
    
    Examples:
    - "What's happening in Tokyo?"  get_events_calendar("Tokyo", "next_month")
    - "Events in Paris next week?"  get_events_calendar("Paris", "next_week")
    - "Things to do in Dubai?"  get_events_calendar("Dubai", "next_month")"""
)
def get_events_calendar(location: str, timeframe: str = "next_month") -> str:
    """Get events and activities calendar for a location."""
    return f"Events in {location} ({timeframe}): Music Festival (June 5), Food Market (every weekend), Art Exhibition (ongoing)"

def query_timeseries_data_legacy(
    data_type: str,
    location: str,
    timeframe: str = "next_week",
) -> str:
    """LEGACY - Use @ai_function decorated functions above instead."""
    
    
    if data_type == "weather_forecast":
        return _query_weather_api(location, timeframe)
    
    elif data_type == "historical_weather":
        return _query_historical_weather_db(location, timeframe)
    
    elif data_type == "hotel_prices":
        return _query_hotel_price_db(location, timeframe)
    
    elif data_type == "flight_prices":
        return _query_flight_price_api(location, timeframe)
    
    elif data_type == "tourist_volume":
        return _query_analytics_db(location, timeframe)
    
    elif data_type == "event_calendar":
        return _query_events_api(location, timeframe)
    
    else:
        return f"Data type '{data_type}' not supported. Available types: weather_forecast, historical_weather, hotel_prices, flight_prices, tourist_volume, event_calendar"

def _query_weather_api(location: str, timeframe: str) -> str:
    """Route to OpenWeatherMap or similar API"""
    api_key = os.environ.get("OPENWEATHER_API_KEY")
    
    
    return f"[MOCK] Weather forecast for {location} ({timeframe}): Sunny, 5°C average"
def _query_historical_weather_db(location: str, timeframe: str) -> str:
    """Route to historical weather database (e.g., TimescaleDB, InfluxDB)"""
    return f"[MOCK] Historical weather for {location} ({timeframe}): Average °C, mostly clear"
def _query_hotel_price_db(location: str, timeframe: str) -> str:
    """Route to hotel pricing database or API"""
    return f"[MOCK] Hotel prices in {location} ({timeframe}): $80-50/night average"
def _query_flight_price_api(location: str, timeframe: str) -> str:
    """Route to flight price API (e.g., Skyscanner, Amadeus)"""
    return f"[MOCK] Flight prices to {location} ({timeframe}): $00-500 average"
def _query_analytics_db(location: str, timeframe: str) -> str:
    """Route to tourist analytics database"""
    return f"[MOCK] Tourist volume in {location} ({timeframe}): High season, 0K+ daily visitors"
def _query_events_api(location: str, timeframe: str) -> str:
    """Route to events/calendar API"""
    return f"[MOCK] Events in {location} ({timeframe}): Music Festival (June 5), Food Fair (June 0)"
"""
How the agent uses this tool:

User: "What's the weather going to be like in Paris next month?"
Agent thinks: Need weather_forecast data for Paris, next_month
Agent calls: query_timeseries_data("weather_forecast", "Paris", "next_month")
Tool routes: Calls OpenWeatherMap API
Agent receives: Weather data
Agent responds: "Paris will have mild weather next month, averaging 5°C with mostly sunny days."

User: "Are hotel prices in Tokyo expensive right now?"
Agent thinks: Need hotel_prices data for Tokyo, current timeframe
Agent calls: query_timeseries_data("hotel_prices", "Tokyo", "next_week")
Tool routes: Queries hotel pricing database
Agent receives: Price data
Agent responds: "Hotel prices in Tokyo are moderate right now, averaging $80-50/night."

KEY BENEFITS:
. Agent decides WHAT data is needed (semantic understanding)
. Tool decides HOW to get it (technical routing)
. Separation of concerns: AI handles intent, tool handles implementation
4. Easy to add new data sources without retraining agent
"""
