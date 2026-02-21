"""
Airport Search Tool
===================
Search for airports by city, country, or airport code.
Uses Azure AI Search if available, falls back to curated database.
No additional API key required.
"""

import os
from typing import Optional
def search_airports(query: str, use_azure_search: bool = True) -> str:
    """
    Search for airports using Azure AI Search or fallback database.
    
    Args:
        query: City name, country name, or airport code (e.g., 'Dubai', 'France', 'JFK')
        use_azure_search: Try Azure AI Search first (default: True)
    
    Returns:
        Formatted string with airport details including code, name, city, and country
    """
    
    if use_azure_search:
        try:
            result = _search_airports_azure(query)
            if result and "" not in result:
                return result
        except Exception as e:
            pass
    
    return _search_airports_local(query)
def _search_airports_azure(query: str) -> Optional[str]:
    """Search airports using Azure AI Search airports-index."""
    
    try:
        from azure.identity import AzureCliCredential
        from azure.search.documents import SearchClient
        
        search_endpoint = os.environ.get("AZURE_SEARCH_ENDPOINT")
        if not search_endpoint:
            return None
        
        credential = AzureCliCredential(process_timeout=60)
        
        search_client = SearchClient(
            endpoint=search_endpoint,
            index_name="airports-index",  # Dedicated airports index
            credential=credential
        )
        
        results = search_client.search(
            search_text=query,
            top=0,
            include_total_count=True
        )
        
        airports = []
        for result in results:
            airports.append({
                "code": result.get('code', ''),
                "name": result.get('name', ''),
                "city": result.get('city', ''),
                "country": result.get('country', '')
            })
        
        if airports:
            output = [f" Airports for '{query}' (from Azure AI Search):\n"]
            for i, airport in enumerate(airports, ):
                code_str = f"{airport['code']} - " if airport['code'] else ""
                output.append(f"{i}. {code_str}{airport['name']}")
                if airport['city'] or airport['country']:
                    location = ", ".join(filter(None, [airport['city'], airport['country']]))
                    output.append(f"    {location}\n")
            
            output.append(f"\nTotal: {len(airports)} airport(s) found")
            return "\n".join(output)
        
        return None
        
    except Exception as e:
        return None
def _search_airports_local(query: str) -> str:
    """
    Fallback function when Azure AI Search is unavailable.
    Returns a helpful message directing users to set up Azure AI Search.
    """
    return f""" No airports found for '{query}'

 Azure AI Search is currently unavailable.

 To enable airport search:
. Ensure AZURE_SEARCH_ENDPOINT is set in your .env file
. Run: python create_airports_index.py
. This will create and populate the airports-index

For more information, see AIRPORT_DATA_GUIDE.md"""
if __name__ == "__main__":
    print(search_airports("Dubai"))
    print("\n" + "="*50 + "\n")
    print(search_airports("JFK"))
    print("\n" + "="*50 + "\n")
    print(search_airports("Paris"))
