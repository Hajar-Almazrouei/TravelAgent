"""
MCP Server: API Gateway
========================

This is a proper MCP server that exposes external API tools (currency, directions, weather).
It can be:
1. Used locally via stdio with MCPStdioTool
2. Hosted as HTTP endpoint for Azure AI Foundry's HostedMCPTool

Based on: https://modelcontextprotocol.io/docs/tools/hosting
"""

import os
import sys
from pathlib import Path

import requests
from dotenv import load_dotenv
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

# Import our custom tools
from airport_tool import search_airports


env_path = Path(__file__).parent.parent.parent.parent / ".env"
load_dotenv(env_path)

EXCHANGERATE_API_KEY = os.getenv("EXCHANGERATE_API_KEY", "")
OPENROUTESERVICE_API_KEY = os.getenv("OPENROUTESERVICE_API_KEY", "")
WTTR_IN_ENABLED = os.getenv("WTTR_IN_ENABLED", "true").lower() == "true"

app = Server("api-gateway")


@app.list_tools()
async def list_tools() -> list[Tool]:
    """List available MCP tools."""
    return [
        Tool(
            name="convert_currency",
            description="Convert currency using real-time exchange rates",
            inputSchema={
                "type": "object",
                "properties": {
                    "amount": {
                        "type": "number",
                        "description": "Amount to convert"
                    },
                    "from_currency": {
                        "type": "string",
                        "description": "Source currency code (USD, EUR, etc.)"
                    },
                    "to_currency": {
                        "type": "string",
                        "description": "Target currency code (USD, EUR, etc.)"
                    }
                },
                "required": ["amount", "from_currency", "to_currency"]
            }
        ),
        Tool(
            name="estimate_flight_time",
            description="Estimate flight duration between two cities or airports",
            inputSchema={
                "type": "object",
                "properties": {
                    "origin": {
                        "type": "string",
                        "description": "Starting city or airport (e.g., 'Dubai', 'JFK', 'Paris')"
                    },
                    "destination": {
                        "type": "string",
                        "description": "Destination city or airport (e.g., 'London', 'LAX', 'Tokyo')"
                    }
                },
                "required": ["origin", "destination"]
            }
        ),
        Tool(
            name="search_airports",
            description="Search for airports by city, country, or get airport details by code",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "City name, country name, or airport code (e.g., 'Dubai', 'France', 'JFK')"
                    }
                },
                "required": ["query"]
            }
        ),
        Tool(
            name="check_visa_requirements",
            description="Check visa requirements for traveling from one country to another",
            inputSchema={
                "type": "object",
                "properties": {
                    "from_country": {
                        "type": "string",
                        "description": "Passport/nationality country (e.g., 'UAE', 'United States', 'India')"
                    },
                    "to_country": {
                        "type": "string",
                        "description": "Destination country (e.g., 'France', 'Japan', 'UK')"
                    }
                },
                "required": ["from_country", "to_country"]
            }
        ),
        Tool(
            name="get_detailed_weather",
            description="Get detailed weather forecast using wttr.in (completely free, no API key needed)",
            inputSchema={
                "type": "object",
                "properties": {
                    "location": {
                        "type": "string",
                        "description": "City name or location"
                    }
                },
                "required": ["location"]
            }
        ),
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    """Execute MCP tool."""
    
    print(f"🔧 Tool: {name}", file=sys.stderr, flush=True)
    
    if name == "convert_currency":
        result = convert_currency(
            arguments["amount"],
            arguments["from_currency"],
            arguments["to_currency"]
        )
    elif name == "estimate_flight_time":
        result = estimate_flight_time(
            arguments["origin"],
            arguments["destination"]
        )
    elif name == "search_airports":
        result = search_airports(
            arguments["query"]
        )
    elif name == "get_detailed_weather":
        result = get_detailed_weather(
            arguments["location"]
        )
    else:
        result = f"❌ Unknown tool: {name}"
    
    return [TextContent(type="text", text=result)]


def convert_currency(amount: float, from_currency: str, to_currency: str) -> str:
    """Convert currency using real-time exchange rates."""
    
    if not EXCHANGERATE_API_KEY:
        return "❌ ExchangeRate API key not configured"
    
    try:
        url = f"https://v6.exchangerate-api.com/v6/{EXCHANGERATE_API_KEY}/pair/{from_currency.upper()}/{to_currency.upper()}/{amount}"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if data["result"] != "success":
            return f"❌ Error: {data.get('error-type', 'Unknown')}"
        
        return f"""💱 {amount:,.2f} {from_currency.upper()} = {data['conversion_result']:,.2f} {to_currency.upper()}
📊 Rate: 1 {from_currency.upper()} = {data['conversion_rate']:.4f} {to_currency.upper()}
🕐 Updated: {data.get('time_last_update_utc', 'N/A')}"""
        
    except Exception as e:
        return f"❌ Error: {str(e)}"


def estimate_flight_time(origin: str, destination: str) -> str:
    """Estimate flight time between two cities using great circle distance."""
    
    try:
        from math import radians, sin, cos, sqrt, atan2, asin
        
        # Use Nominatim for geocoding (free, no API key)
        def geocode_city(location: str) -> tuple:
            url = "https://nominatim.openstreetmap.org/search"
            response = requests.get(url, params={
                "q": location,
                "format": "json",
                "limit": 1
            }, headers={
                "User-Agent": "TravelAgent/1.0"
            }, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if not data:
                raise ValueError(f"Location not found: {location}")
            
            result = data[0]
            lat = float(result["lat"])
            lon = float(result["lon"])
            name = result.get("display_name", location).split(",")[0]
            
            return lat, lon, name
        
        # Geocode both cities
        origin_lat, origin_lon, origin_name = geocode_city(origin)
        dest_lat, dest_lon, dest_name = geocode_city(destination)
        
        # Calculate great circle distance (Haversine formula)
        R = 6371  # Earth radius in km
        lat1, lon1, lat2, lon2 = map(radians, [origin_lat, origin_lon, dest_lat, dest_lon])
        
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
        c = 2 * asin(sqrt(a))
        distance_km = R * c
        
        # Estimate flight time (average commercial jet speed ~800 km/h)
        # Add 30 min for takeoff/landing
        cruise_speed = 800  # km/h
        flight_time_hours = (distance_km / cruise_speed) + 0.5
        
        hours = int(flight_time_hours)
        minutes = int((flight_time_hours - hours) * 60)
        
        # Categorize flight
        if distance_km < 1500:
            flight_type = "Short-haul"
            emoji = "✈️"
        elif distance_km < 4000:
            flight_type = "Medium-haul"
            emoji = "🛫"
        else:
            flight_type = "Long-haul"
            emoji = "🌍"
        
        return f"""{emoji} Flight Estimate: {origin_name} → {dest_name}
📏 Distance: {distance_km:,.0f} km
⏱️ Flight Time: ~{hours}h {minutes}m
🎫 Type: {flight_type} flight
💡 Note: Actual time may vary with wind, routing, and aircraft type"""
        
    except Exception as e:
        return f" Error: {str(e)}"


def get_detailed_weather(location: str) -> str:
    """Get weather using wttr.in (free, no API key needed)."""
    
    if not WTTR_IN_ENABLED:
        return " wttr.in weather service is disabled"
    
    try:
        # wttr.in provides free weather data without API key
        url = f"https://wttr.in/{location}"
        response = requests.get(url, params={
            "format": "j1",  # JSON format
        }, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        current = data["current_condition"][0]
        
        result = f"""🌤️ Weather in {location}:
🌡️ {current['temp_C']}°C (feels like {current['FeelsLikeC']}°C)
☁️ {current['weatherDesc'][0]['value']}
💧 Humidity: {current['humidity']}%
💨 Wind: {current['windspeedKmph']} km/h {current['winddir16Point']}
👁️ Visibility: {current['visibility']} km
☂️ Precipitation: {current['precipMM']} mm"""
        
        return result
        
    except Exception as e:
        return f"❌ Error: {str(e)}"


async def main():
    """Run MCP server via stdio."""
    async with stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            app.create_initialization_options()
        )


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())