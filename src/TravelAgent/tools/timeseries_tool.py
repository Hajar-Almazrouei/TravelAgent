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
    description="""Get 5-16 day weather forecast with temperature, precipitation, and conditions for any city worldwide.
    
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
    - "Weather in Tokyo?" → get_weather_forecast("Tokyo", 5)
    - "Will it rain in Paris next week?" → get_weather_forecast("Paris", 7)"""
)
def get_weather_forecast(location: str, days: int = 5) -> str:
    """
    Get weather forecast for a specific location using Open-Meteo API.
    Returns time series data including temperature, precipitation, and conditions.
    """
    try:
        # Step 1: Geocode location to get coordinates
        geocode_url = f"https://geocoding-api.open-meteo.com/v1/search?name={location}&count=1&language=en&format=json"
        
        with httpx.Client(timeout=10.0) as client:
            geocode_response = client.get(geocode_url)
            geocode_data = geocode_response.json()
            
            if not geocode_data.get("results"):
                return f"Could not find location: {location}. Please try a different city name."
            
            # Get coordinates
            lat = geocode_data["results"][0]["latitude"]
            lon = geocode_data["results"][0]["longitude"]
            location_name = geocode_data["results"][0]["name"]
            country = geocode_data["results"][0].get("country", "")
            
            # Step 2: Get weather forecast
            weather_url = (
                f"https://api.open-meteo.com/v1/forecast?"
                f"latitude={lat}&longitude={lon}"
                f"&daily=temperature_2m_max,temperature_2m_min,precipitation_sum,weathercode"
                f"&forecast_days={min(days, 16)}"  # API supports max 16 days
                f"&timezone=auto"
            )
            
            weather_response = client.get(weather_url)
            weather_data = weather_response.json()
            
            # Step 3: Format response
            daily = weather_data["daily"]
            forecast_lines = [f"Weather forecast for {location_name}, {country}:\n"]
            
            # Weather code mapping
            weather_codes = {
                0: "Clear sky", 1: "Mainly clear", 2: "Partly cloudy", 3: "Overcast",
                45: "Foggy", 48: "Foggy", 51: "Light drizzle", 53: "Drizzle", 
                55: "Heavy drizzle", 61: "Light rain", 63: "Rain", 65: "Heavy rain",
                71: "Light snow", 73: "Snow", 75: "Heavy snow", 95: "Thunderstorm"
            }
            
            for i in range(len(daily["time"])):
                date = daily["time"][i]
                temp_max = daily["temperature_2m_max"][i]
                temp_min = daily["temperature_2m_min"][i]
                precip = daily["precipitation_sum"][i]
                code = daily["weathercode"][i]
                condition = weather_codes.get(code, "Unknown")
                
                forecast_lines.append(
                    f"📅 {date}: {condition}, {temp_min:.1f}°C - {temp_max:.1f}°C, "
                    f"Precipitation: {precip}mm"
                )
            
            return "\n".join(forecast_lines)
            
    except Exception as e:
        return f"Error fetching weather data: {str(e)}"