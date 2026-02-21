"""
Azure AI Search Tool - Search through indexed travel data
Uses Azure Cognitive Search to query travel information, destinations, and recommendations
"""
from agent_framework import ai_function
import os
from azure.identity import AzureCliCredential
from azure.search.documents import SearchClient
from typing import Optional
@ai_function(
    name="search_travel_info",
    description="REQUIRED: Search the indexed travel database whenever user asks about destinations, places, or travel info. Use when user says 'search', 'find', 'database', 'tell me about [place]', or asks for destination information. Returns data from the travel-index with budget levels, climate info, and descriptions."
)
def search_travel_info(query: str, top_results: int = 5) -> str:
    """
    Search Azure AI Search index for travel-related information.
    Returns relevant documents from the indexed travel database.
    """
    print(f"\n [AI SEARCH] Calling search_travel_info with query: '{query}'")
    try:

        search_endpoint = os.environ.get("AZURE_SEARCH_ENDPOINT")
        index_name = os.environ.get("AZURE_SEARCH_INDEX_NAME", "travel-index")
        

        if not search_endpoint:
            return (
                "Azure AI Search is not configured. Please set:\n"
                "- AZURE_SEARCH_ENDPOINT in .env\n"
                "- AZURE_SEARCH_INDEX_NAME in .env (optional, defaults to 'travel-index')\n\n"
                "Authentication uses AzureCliCredential (same as your agent) - no keys needed!"
            )

        credential = AzureCliCredential(process_timeout=60)
        
        search_client = SearchClient(
            endpoint=search_endpoint,
            index_name=index_name,
            credential=credential
        )
        
        results = search_client.search(
            search_text=query,
            top=top_results,
            include_total_count=True
        )
        
        formatted_results = [f"Search results for: '{query}'\n"]
        
        result_count = 0
        for result in results:
            result_count += 
            title = result.get('title', result.get('name', 'Untitled'))
            content = result.get('content', result.get('description', ''))
            location = result.get('location', '')
            score = result.get('@search.score', 0)
            
            formatted_results.append(
                f"\n Result {result_count} (Relevance: {score:.f}):\n"
                f"   Title: {title}\n"
                f"   {f'Location: {location}' if location else ''}\n"
                f"   {content[:00]}{'...' if len(content) > 00 else ''}\n"
            )
        
        if result_count == 0:
            return f"No results found for '{query}'. Try different search terms."
        
        return "\n".join(formatted_results) + f"\n\nTotal results: {result_count}"
        
    except Exception as e:
        return f"Error searching travel database: {str(e)}"
@ai_function(
    name="search_destinations_by_criteria",
    description="REQUIRED: Search travel database by filters (climate, budget, season). Use when user asks about 'budget level', 'climate type', 'best season', or wants filtered results like 'expensive destinations', 'tropical places', 'spring travel'. Returns filtered results from travel-index."
)
def search_destinations_by_criteria(
    climate: Optional[str] = None,
    budget: Optional[str] = None,
    activities: Optional[str] = None,
    season: Optional[str] = None
) -> str:
    """
    Search for destinations using filters and criteria.
    Supports filtering by climate, budget level, preferred activities, and travel season.
    """
    print(f"\n [AI SEARCH] Calling search_destinations_by_criteria - climate:{climate}, budget:{budget}, season:{season}")
    try:
        search_endpoint = os.environ.get("AZURE_SEARCH_ENDPOINT")
        index_name = os.environ.get("AZURE_SEARCH_INDEX_NAME", "travel-index")
        
        if not search_endpoint:
            return "Azure AI Search is not configured. Please add AZURE_SEARCH_ENDPOINT to .env file."
        
        filters = []
        if climate:
            filters.append(f"climate eq '{climate}'")
        if budget:
            filters.append(f"budget_level eq '{budget}'")
        if season:
            filters.append(f"best_season eq '{season}'")
        
        filter_str = " and ".join(filters) if filters else None
        
        search_text = activities if activities else "*"
        
        credential = AzureCliCredential(process_timeout=60)
        search_client = SearchClient(
            endpoint=search_endpoint,
            index_name=index_name,
            credential=credential
        )
        
        results = search_client.search(
            search_text=search_text,
            filter=filter_str,
            top=5
        )
        
        criteria_text = []
        if climate: criteria_text.append(f"Climate: {climate}")
        if budget: criteria_text.append(f"Budget: {budget}")
        if activities: criteria_text.append(f"Activities: {activities}")
        if season: criteria_text.append(f"Season: {season}")
        
        formatted_results = [
            f"Destinations matching criteria:",
            f"  {', '.join(criteria_text)}\n"
        ]
        
        result_count = 0
        for result in results:
            result_count += 
            name = result.get('name', result.get('title', 'Unknown'))
            description = result.get('description', result.get('content', ''))
            
            formatted_results.append(
                f"\n {result_count}. {name}\n"
                f"   {description[:50]}{'...' if len(description) > 50 else ''}\n"
            )
        
        if result_count == 0:
            return f"No destinations found matching your criteria. Try adjusting your preferences."
        
        return "\n".join(formatted_results)
        
    except Exception as e:
        return f"Error searching by criteria: {str(e)}"

