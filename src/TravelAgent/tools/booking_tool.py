"""
Booking.com API Integration Tool - Real-time hotel and flight data
Uses RapidAPI's Booking.com API for live pricing and availability.

API Host: booking-com.p.rapidapi.com
API Documentation: https://rapidapi.com/apidojo/api/booking-com

Required Environment Variables:
- RAPIDAPI_KEY: Your RapidAPI key
- RAPIDAPI_HOST: booking-com.p.rapidapi.com
"""
import os
import httpx
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
from agent_framework import ai_function
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(filename)s:%(lineno)d - %(levelname)s - %(message)s'
)
logger = logging.getLogger("booking-tool")

RAPIDAPI_KEY = os.getenv("RAPIDAPI_KEY")
RAPIDAPI_HOST = os.getenv("RAPIDAPI_HOST", "booking-com.p.rapidapi.com")


def _make_booking_api_request_sync(
    endpoint: str, 
    params: Optional[Dict[str, str]] = None
) -> Dict[str, Any]:
    """Make a sync request to the Booking.com API via RapidAPI."""
    if not RAPIDAPI_KEY:
        logger.error("RAPIDAPI_KEY not set")
        return {"error": "RAPIDAPI_KEY environment variable not set. Please add it to your .env file."}
    
    url = f"https://{RAPIDAPI_HOST}{endpoint}"
    headers = {
        "x-rapidapi-key": RAPIDAPI_KEY,
        "x-rapidapi-host": RAPIDAPI_HOST
    }
    
    logger.info(f"Making API request to {url} with params: {params}")
    
    with httpx.Client(timeout=30.0) as client:
        try:
            response = client.get(url, headers=headers, params=params)
            response.raise_for_status()
            logger.info(f"API request to {endpoint} successful")
            return response.json()
        except httpx.TimeoutException:
            logger.error(f"Timeout on request to {endpoint}")
            return {"error": "Request timed out. Please try again."}
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error on request to {endpoint}: {e}")
            logger.error(f"Response status: {e.response.status_code}, URL: {e.response.url}")
            logger.error(f"Request params that caused error: {params}")
            return {"error": f"HTTP error: {e.response.status_code}. The dates provided may be invalid (must be in the future) or the destination may not be available."}
        except Exception as e:
            logger.error(f"API request to {endpoint} failed: {str(e)}")
            return {"error": str(e)}


@ai_function(
    name="search_hotel_destinations",
    description="""Search for hotel destinations on Booking.com by city/location name.
    
    CALL THIS FIRST when user asks about hotels - you need the dest_id for hotel searches.
    
    Use when:
    - User wants to search hotels in a city/location
    - Need to get destination ID before searching for hotels
    - "Find hotels in Paris"
    - "Search accommodation in Tokyo"
    
    Returns: List of matching destinations with their dest_id values.
    The dest_id is needed for the search_hotels function.
    
    Examples:
    - "Hotels in Paris" → search_hotel_destinations("Paris")
    - "Where to stay in Tokyo" → search_hotel_destinations("Tokyo")"""
)
def search_hotel_destinations(query: str) -> str:
    """
    Search for hotel destinations by name using Booking.com API.
    Returns destination IDs needed for hotel searches.
    
    Args:
        query: The destination to search for (e.g., "Paris", "New York", "Tokyo")
    """
    logger.info(f"Searching for destinations with query: {query}")
    
    endpoint = "/v1/hotels/locations"
    params = {
        "name": query,
        "locale": "en-gb"
    }
    
    result = _make_booking_api_request_sync(endpoint, params)
    
    if "error" in result:
        return f"Error searching destinations: {result['error']}"
    
    if isinstance(result, list):
        destinations_count = len(result)
        logger.info(f"Found {destinations_count} destinations for query: {query}")
        
        if destinations_count == 0:
            return f"No destinations found matching '{query}'. Try a different city name."
        
        formatted_results = [f"🔍 Found {destinations_count} destinations matching '{query}':\n"]
        
        for destination in result[:5]:  
            dest_id = destination.get('dest_id', 'N/A')
            dest_type = destination.get('dest_type', 'Unknown')
            name = destination.get('name', 'Unknown')
            label = destination.get('label', '')
            city_name = destination.get('city_name', '')
            country = destination.get('country', '')
            
            dest_info = (
                f"  {name}\n"
                f"   Label: {label}\n"
                f"   Type: {dest_type}\n"
                f"   Destination ID: {dest_id}\n"
                f"   City: {city_name}\n"
                f"   Country: {country}\n"
            )
            formatted_results.append(dest_info)
        
        formatted_results.append("\n Use the Destination ID with search_hotels to get hotel listings.")
        return "\n".join(formatted_results)
    else:
        logger.warning(f"Unexpected response format from API for query: {query}")
        return f"Unexpected response format. Response: {str(result)[:200]}"


@ai_function(
    name="search_hotels",
    description="""Get real-time hotel listings with prices from Booking.com for a destination.
    
    IMPORTANT: You need a dest_id first - use search_hotel_destinations to get it.
    
    Use when:
    - User wants hotel prices and availability
    - "What hotels are available in [location]?"
    - "Find me hotels for my trip"
    - "How much are hotels in [location]?"
    - "Best hotels in [location]"
    
    Returns: Hotel names, ratings, prices, and details.
    Prices are real-time from Booking.com.
    
    Parameters:
    - dest_id: Get this from search_hotel_destinations first
    - dest_type: Usually "city" (from search_hotel_destinations)
    - checkin_date: Format YYYY-MM-DD (defaults to tomorrow)
    - checkout_date: Format YYYY-MM-DD (defaults to day after tomorrow)
    - adults: Number of adult guests (default 2)
    
    Examples:
    - search_hotels("-1456928", "city", "2025-01-15", "2025-01-18", 2)"""
)
def search_hotels(
    dest_id: str,
    dest_type: str = "city",
    checkin_date: Optional[str] = None,
    checkout_date: Optional[str] = None,
    adults: int = 2,
    room_qty: int = 1
) -> str:
    """
    Get hotels for a specific destination from Booking.com with real-time prices.
    
    Args:
        dest_id: The destination ID from search_hotel_destinations
        dest_type: Destination type (city, region, landmark, etc.)
        checkin_date: Check-in date in YYYY-MM-DD format (defaults to tomorrow)
        checkout_date: Check-out date in YYYY-MM-DD format (defaults to day after tomorrow)
        adults: Number of adults (default: 2)
        room_qty: Number of rooms (default: 1)
    """
    # Default dates if not provided - always use current time
    today = datetime.now()
    if not checkin_date or checkin_date < today.strftime("%Y-%m-%d"):
        checkin_date = (today + timedelta(days=1)).strftime("%Y-%m-%d")
        logger.info(f"No valid checkin_date provided, using tomorrow: {checkin_date}")
    if not checkout_date or checkout_date <= checkin_date:
        try:
            checkin_dt = datetime.strptime(checkin_date, "%Y-%m-%d")
            checkout_date = (checkin_dt + timedelta(days=3)).strftime("%Y-%m-%d")
            logger.info(f"No valid checkout_date provided, using checkin + 3 days: {checkout_date}")
        except:
            checkout_date = (today + timedelta(days=4)).strftime("%Y-%m-%d")
    
    logger.info(f"Searching hotels: dest_id={dest_id}, checkin={checkin_date}, checkout={checkout_date}, adults={adults}")
    
    try:
        checkin_dt = datetime.strptime(checkin_date, "%Y-%m-%d")
        checkout_dt = datetime.strptime(checkout_date, "%Y-%m-%d")
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        
        logger.info(f"Date validation - Today: {today.date()}, Check-in: {checkin_dt.date()}, Check-out: {checkout_dt.date()}")
        
        if checkin_dt < today:
            logger.warning(f"⚠️ Check-in date {checkin_date} is in the past! Adjusting to tomorrow")
            checkin_dt = today + timedelta(days=1)
            checkin_date = checkin_dt.strftime("%Y-%m-%d")
            checkout_dt = checkin_dt + timedelta(days=3)
            checkout_date = checkout_dt.strftime("%Y-%m-%d")
            logger.info(f"✅ Adjusted dates - Check-in: {checkin_date}, Check-out: {checkout_date}")
        
        if checkout_dt <= checkin_dt:
            logger.warning(f"⚠️ Check-out date {checkout_date} is before or equal to check-in, adjusting")
            checkout_dt = checkin_dt + timedelta(days=3)
            checkout_date = checkout_dt.strftime("%Y-%m-%d")
            logger.info(f"✅ Adjusted check-out to: {checkout_date}")
    except ValueError as e:
        logger.error(f"❌ Invalid date format: {e}")
        return f"Error: Invalid date format. Please use YYYY-MM-DD (e.g., 2025-12-10)"
    
    logger.info(f"🔄 Final validated dates being sent to API - Check-in: {checkin_date}, Check-out: {checkout_date}")
    
    endpoint = "/v1/hotels/search"
    params = {
        "dest_id": dest_id,
        "dest_type": dest_type,
        "checkin_date": checkin_date,
        "checkout_date": checkout_date,
        "adults_number": str(adults),
        "room_number": str(room_qty),
        "order_by": "popularity",
        "locale": "en-gb",
        "units": "metric",
        "filter_by_currency": "USD"
    }
    
    result = _make_booking_api_request_sync(endpoint, params)
    
    if "error" in result:
        return f"Error fetching hotels: {result['error']}"
    
    formatted_results = []
    
    hotels = result.get("result", [])
    
    if isinstance(hotels, list) and len(hotels) > 0:
        hotels_count = len(hotels)
        logger.info(f"Found {hotels_count} hotels for destination: {dest_id}")
        
        formatted_results.append(f"🏨 Found {hotels_count} hotels ({checkin_date} to {checkout_date}, {adults} adults):\n")
        
        for hotel in hotels[:10]:  # Limit to 10 hotels
            hotel_name = hotel.get('hotel_name', 'Unknown Hotel')
            address = hotel.get('address', 'Unknown')
            city = hotel.get('city', '')
            
            hotel_info = [
                f"🏨 {hotel_name}",
                f"   📍 {address}, {city}",
            ]
            
            # Rating
            review_score = hotel.get('review_score')
            if review_score:
                review_word = hotel.get('review_score_word', '')
                review_count = hotel.get('review_nr', 0)
                hotel_info.append(f"   ⭐ Rating: {review_score}/10 {review_word} ({review_count} reviews)")
            
            # Star rating
            hotel_class = hotel.get('class')
            if hotel_class:
                hotel_info.append(f"   🌟 Stars: {'⭐' * int(hotel_class)}")
            
            # Pricing
            price_breakdown = hotel.get('price_breakdown', {})
            gross_price = price_breakdown.get('gross_price')
            currency = hotel.get('currency_code', price_breakdown.get('currency', 'USD'))
            
            if gross_price:
                hotel_info.append(f"   💰 Price: {currency} {gross_price}")
            else:
                # Try alternate price field
                min_price = hotel.get('min_total_price')
                if min_price:
                    hotel_info.append(f"   💰 Price: {currency} {min_price}")
                else:
                    hotel_info.append("   💰 Price: Check availability")
            
            # Distance from center
            distance = hotel.get('distance_to_cc')
            if distance:
                hotel_info.append(f"   📏 Distance from center: {distance} km")
            
            # Free cancellation
            if hotel.get('is_free_cancellable'):
                hotel_info.append("   ✅ Free cancellation available")
            
            # Hotel URL
            url = hotel.get('url')
            if url:
                hotel_info.append(f"   🔗 Book: https://www.booking.com{url}")
            
            formatted_results.append("\n".join(hotel_info))
            formatted_results.append("")  # Empty line between hotels
        
        return "\n".join(formatted_results)
    else:
        logger.warning(f"No hotels found or unexpected response format for destination: {dest_id}")
        return f"No hotels found for these dates ({checkin_date} to {checkout_date}). Try different dates or destination."


@ai_function(
    name="get_hotel_prices_live",
    description="""Get REAL-TIME hotel prices from Booking.com for any location.
    
    This is a convenience function that combines destination search and hotel search.
    Use this instead of the mock get_hotel_prices for accurate, live pricing.
    
    ALWAYS prefer this over mock data when user asks:
    - "How much are hotels in [location]?"
    - "What's the average hotel price in [location]?"
    - "Is accommodation expensive in [location]?"
    - "Hotel costs for my trip to [location]"
    
    Returns: Real hotel listings with actual prices from Booking.com
    
    Examples:
    - "Hotel prices in Tokyo?" → get_hotel_prices_live("Tokyo", "2025-01-15", "2025-01-18")
    - "How expensive is Dubai?" → get_hotel_prices_live("Dubai")"""
)
def get_hotel_prices_live(
    location: str,
    checkin_date: Optional[str] = None,
    checkout_date: Optional[str] = None,
    adults: int = 2
) -> str:
    """
    Get real-time hotel prices for a location - combines destination search and hotel lookup.
    
    Args:
        location: City or destination name (e.g., "Paris", "Tokyo")
        checkin_date: Check-in date YYYY-MM-DD (defaults to tomorrow)
        checkout_date: Check-out date YYYY-MM-DD (defaults to day after tomorrow)
        adults: Number of adults (default: 2)
    """
    logger.info(f"Getting hotel prices for {location}")
    
    dest_endpoint = "/v1/hotels/locations"
    dest_params = {
        "name": location,
        "locale": "en-gb"
    }
    
    dest_result = _make_booking_api_request_sync(dest_endpoint, dest_params)
    
    if "error" in dest_result:
        return f"Error finding destination: {dest_result['error']}"
    
    if not isinstance(dest_result, list) or len(dest_result) == 0:
        return f"Could not find destination '{location}'. Please try a different city name."
    
    destination = dest_result[0]
    dest_id = destination.get("dest_id")
    dest_type = destination.get("dest_type", "city")
    destination_name = destination.get("name", location)
    
    if not dest_id:
        return f"Could not get destination ID for '{location}'."
    
    logger.info(f"Found destination: {destination_name} (ID: {dest_id}, Type: {dest_type})")
    
    today = datetime.now()
    if not checkin_date or checkin_date < today.strftime("%Y-%m-%d"):
        checkin_date = (today + timedelta(days=1)).strftime("%Y-%m-%d")
        logger.info(f"Using default checkin_date (tomorrow): {checkin_date}")
    if not checkout_date or checkout_date <= checkin_date:
        try:
            checkin_dt = datetime.strptime(checkin_date, "%Y-%m-%d")
            checkout_date = (checkin_dt + timedelta(days=3)).strftime("%Y-%m-%d")
            logger.info(f"Using default checkout_date (checkin + 3 days): {checkout_date}")
        except:
            checkout_date = (today + timedelta(days=4)).strftime("%Y-%m-%d")
    
    # Now search for hotels
    return search_hotels(dest_id, dest_type, checkin_date, checkout_date, adults)


@ai_function(
    name="search_flights",
    description="""Search for real-time flight prices.
    
    Note: The Booking.com API primarily focuses on hotels. 
    For flights, consider using dedicated flight APIs.
    
    Use when:
    - "How much are flights to [destination]?"
    - "Find flights from [origin] to [destination]"
    
    Returns: Flight search guidance or results if available."""
)
def search_flights(
    origin: str,
    destination: str,
    departure_date: Optional[str] = None,
    return_date: Optional[str] = None,
    adults: int = 1
) -> str:
    """
    Search for flights - note that Booking.com API focuses on hotels.
    
    Args:
        origin: Origin city or airport
        destination: Destination city or airport
        departure_date: Departure date YYYY-MM-DD
        return_date: Return date YYYY-MM-DD (optional)
        adults: Number of passengers
    """
    if not departure_date:
        departure_date = (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d")
    
    return (
        f"✈️ Flight search from {origin} to {destination} ({departure_date}):\n\n"
        f"ℹ️ The Booking.com API subscription you have focuses on hotels.\n\n"
        f"💡 For flight searches, you can:\n"
        f"1. Use Google Flights: https://www.google.com/flights\n"
        f"2. Use Skyscanner: https://www.skyscanner.com\n"
        f"3. Check airline websites directly\n"
        f"4. Use the Amadeus API for programmatic flight search\n\n"
        f"🏨 Meanwhile, I can help you find hotels in {destination}!"
    )


# ============================================
# Utility Functions
# ============================================

def check_booking_api_status() -> str:
    """Check if the Booking.com API is properly configured and accessible."""
    if not RAPIDAPI_KEY:
        return "❌ RAPIDAPI_KEY not configured. Add it to your .env file."
    
    # Test with a simple static endpoint
    result = _make_booking_api_request_sync("/v1/static/country", {})
    
    if "error" in result:
        return f"❌ API Error: {result['error']}"
    
    if isinstance(result, list) and len(result) > 0:
        return f"✅ Booking.com API is working! Found {len(result)} countries in the database."
    
    return "⚠️ Unexpected API response format."


def get_supported_currencies() -> str:
    """Get list of supported currencies."""
    result = _make_booking_api_request_sync("/v1/static/currency", {})
    
    if "error" in result:
        return f"Error: {result['error']}"
    
    if isinstance(result, list):
        currencies = [f"{c.get('currency', 'N/A')}" for c in result[:20]]
        return f"Supported currencies: {', '.join(currencies)}"
    
    return "Could not fetch currencies."
