"""
Create and populate airports index in Azure AI Search
======================================================
This script creates a dedicated airports index and uploads airport data.
Run this once to set up the index.

Usage:
    python create_airports_index.py
"""

import os
from dotenv import load_dotenv
from azure.identity import AzureCliCredential

load_dotenv()
from azure.search.documents import SearchClient
from azure.search.documents.indexes import SearchIndexClient
from azure.search.documents.indexes.models import (
    SearchIndex,
    SimpleField,
    SearchableField,
    SearchFieldDataType
)
AIRPORTS_DATA = [
    {"id": "DXB", "code": "DXB", "name": "Dubai International Airport", "city": "Dubai", "country": "UAE"},
    {"id": "DWC", "code": "DWC", "name": "Al Maktoum International Airport", "city": "Dubai", "country": "UAE"},
    {"id": "AUH", "code": "AUH", "name": "Abu Dhabi International Airport", "city": "Abu Dhabi", "country": "UAE"},
    {"id": "DOH", "code": "DOH", "name": "Hamad International Airport", "city": "Doha", "country": "Qatar"},
    {"id": "RUH", "code": "RUH", "name": "King Khalid International Airport", "city": "Riyadh", "country": "Saudi Arabia"},
    {"id": "JED", "code": "JED", "name": "King Abdulaziz International Airport", "city": "Jeddah", "country": "Saudi Arabia"},
    
    {"id": "CDG", "code": "CDG", "name": "Charles de Gaulle Airport", "city": "Paris", "country": "France"},
    {"id": "ORY", "code": "ORY", "name": "Orly Airport", "city": "Paris", "country": "France"},
    {"id": "LHR", "code": "LHR", "name": "Heathrow Airport", "city": "London", "country": "UK"},
    {"id": "LGW", "code": "LGW", "name": "Gatwick Airport", "city": "London", "country": "UK"},
    {"id": "STN", "code": "STN", "name": "Stansted Airport", "city": "London", "country": "UK"},
    {"id": "FRA", "code": "FRA", "name": "Frankfurt Airport", "city": "Frankfurt", "country": "Germany"},
    {"id": "AMS", "code": "AMS", "name": "Amsterdam Schiphol Airport", "city": "Amsterdam", "country": "Netherlands"},
    {"id": "FCO", "code": "FCO", "name": "Leonardo da Vinci–Fiumicino Airport", "city": "Rome", "country": "Italy"},
    {"id": "MAD", "code": "MAD", "name": "Adolfo Suárez Madrid-Barajas", "city": "Madrid", "country": "Spain"},
    {"id": "BCN", "code": "BCN", "name": "Barcelona–El Prat Airport", "city": "Barcelona", "country": "Spain"},
    {"id": "IST", "code": "IST", "name": "Istanbul Airport", "city": "Istanbul", "country": "Turkey"},
    {"id": "ZRH", "code": "ZRH", "name": "Zurich Airport", "city": "Zurich", "country": "Switzerland"},
    {"id": "VIE", "code": "VIE", "name": "Vienna International Airport", "city": "Vienna", "country": "Austria"},
    
    {"id": "JFK", "code": "JFK", "name": "John F. Kennedy International", "city": "New York", "country": "USA"},
    {"id": "EWR", "code": "EWR", "name": "Newark Liberty International", "city": "New York", "country": "USA"},
    {"id": "LGA", "code": "LGA", "name": "LaGuardia Airport", "city": "New York", "country": "USA"},
    {"id": "LAX", "code": "LAX", "name": "Los Angeles International", "city": "Los Angeles", "country": "USA"},
    {"id": "ORD", "code": "ORD", "name": "O'Hare International Airport", "city": "Chicago", "country": "USA"},
    {"id": "MIA", "code": "MIA", "name": "Miami International Airport", "city": "Miami", "country": "USA"},
    {"id": "YYZ", "code": "YYZ", "name": "Toronto Pearson International", "city": "Toronto", "country": "Canada"},
    
    {"id": "HND", "code": "HND", "name": "Haneda Airport", "city": "Tokyo", "country": "Japan"},
    {"id": "NRT", "code": "NRT", "name": "Narita International Airport", "city": "Tokyo", "country": "Japan"},
    {"id": "SIN", "code": "SIN", "name": "Singapore Changi Airport", "city": "Singapore", "country": "Singapore"},
    {"id": "HKG", "code": "HKG", "name": "Hong Kong International Airport", "city": "Hong Kong", "country": "Hong Kong"},
    {"id": "BKK", "code": "BKK", "name": "Suvarnabhumi Airport", "city": "Bangkok", "country": "Thailand"},
    {"id": "KUL", "code": "KUL", "name": "Kuala Lumpur International Airport", "city": "Kuala Lumpur", "country": "Malaysia"},
    {"id": "PEK", "code": "PEK", "name": "Beijing Capital International", "city": "Beijing", "country": "China"},
    {"id": "PVG", "code": "PVG", "name": "Shanghai Pudong International", "city": "Shanghai", "country": "China"},
    {"id": "DEL", "code": "DEL", "name": "Indira Gandhi International Airport", "city": "Delhi", "country": "India"},
    {"id": "BOM", "code": "BOM", "name": "Chhatrapati Shivaji Maharaj International", "city": "Mumbai", "country": "India"},
    {"id": "ICN", "code": "ICN", "name": "Incheon International Airport", "city": "Seoul", "country": "South Korea"},
    
    {"id": "SYD", "code": "SYD", "name": "Sydney Kingsford Smith Airport", "city": "Sydney", "country": "Australia"},
    {"id": "MEL", "code": "MEL", "name": "Melbourne Airport", "city": "Melbourne", "country": "Australia"},
    {"id": "AKL", "code": "AKL", "name": "Auckland Airport", "city": "Auckland", "country": "New Zealand"},
    
    {"id": "CAI", "code": "CAI", "name": "Cairo International Airport", "city": "Cairo", "country": "Egypt"},
    {"id": "JNB", "code": "JNB", "name": "O. R. Tambo International Airport", "city": "Johannesburg", "country": "South Africa"},
    
    {"id": "GRU", "code": "GRU", "name": "São Paulo/Guarulhos International", "city": "São Paulo", "country": "Brazil"},
    {"id": "EZE", "code": "EZE", "name": "Ministro Pistarini International", "city": "Buenos Aires", "country": "Argentina"}
]
def create_airports_index():
    """Create the airports index in Azure AI Search."""
    
    search_endpoint = os.environ.get("AZURE_SEARCH_ENDPOINT")
    if not search_endpoint:
        print(" Error: AZURE_SEARCH_ENDPOINT environment variable not set")
        return False
    
    credential = AzureCliCredential(process_timeout=60)
    index_client = SearchIndexClient(endpoint=search_endpoint, credential=credential)
    
    fields = [
        SimpleField(name="id", type=SearchFieldDataType.String, key=True),
        SearchableField(name="code", type=SearchFieldDataType.String, filterable=True, sortable=True),
        SearchableField(name="name", type=SearchFieldDataType.String, filterable=False),
        SearchableField(name="city", type=SearchFieldDataType.String, filterable=True),
        SearchableField(name="country", type=SearchFieldDataType.String, filterable=True, facetable=True)
    ]
    
    index = SearchIndex(name="airports-index", fields=fields)
    
    try:
        print(" Creating airports-index in Azure AI Search...")
        result = index_client.create_or_update_index(index)
        print(f" Index '{result.name}' created successfully!")
        return True
    except Exception as e:
        print(f" Error creating index: {str(e)}")
        return False
def upload_airport_data():
    """Upload airport data to the index."""
    
    search_endpoint = os.environ.get("AZURE_SEARCH_ENDPOINT")
    if not search_endpoint:
        print(" Error: AZURE_SEARCH_ENDPOINT environment variable not set")
        return False
    
    credential = AzureCliCredential(process_timeout=60)
    search_client = SearchClient(
        endpoint=search_endpoint,
        index_name="airports-index",
        credential=credential
    )
    
    try:
        print(f" Uploading {len(AIRPORTS_DATA)} airports to index...")
        result = search_client.upload_documents(documents=AIRPORTS_DATA)
        
        success_count = sum( for r in result if r.succeeded)
        failed_count = len(result) - success_count
        
        print(f" Successfully uploaded {success_count} airports")
        if failed_count > 0:
            print(f"  Failed to upload {failed_count} airports")
        
        return success_count > 0
    except Exception as e:
        print(f" Error uploading data: {str(e)}")
        return False
def verify_index():
    """Verify the index was created and data uploaded successfully."""
    
    search_endpoint = os.environ.get("AZURE_SEARCH_ENDPOINT")
    if not search_endpoint:
        return False
    
    credential = AzureCliCredential(process_timeout=60)
    search_client = SearchClient(
        endpoint=search_endpoint,
        index_name="airports-index",
        credential=credential
    )
    
    try:
        results = search_client.search(search_text="Dubai", top=5)
        airports = list(results)
        
        print(f"\n Verification: Found {len(airports)} results for 'Dubai'")
        for airport in airports:
            print(f"   • {airport['code']} - {airport['name']}, {airport['city']}, {airport['country']}")
        
        return True
    except Exception as e:
        print(f" Verification failed: {str(e)}")
        return False
def main():
    """Main execution flow."""
    
    print("=" * 70)
    print("Azure AI Search - Airports Index Setup")
    print("=" * 70)
    print()
    
    if not create_airports_index():
        print("\n Failed to create index. Exiting.")
        return
    
    print()
    
    if not upload_airport_data():
        print("\n Failed to upload data. Exiting.")
        return
    
    print()
    
    verify_index()
    
    print()
    print("=" * 70)
    print(" Setup complete! You can now use the airports index.")
    print("=" * 70)
    print()
    print("Next steps:")
    print(". The airport_tool.py will automatically use this index")
    print(". You can remove the hardcoded airports_db from the code")
    print(". Test with: python airport_tool.py")
if __name__ == "__main__":
    main()
