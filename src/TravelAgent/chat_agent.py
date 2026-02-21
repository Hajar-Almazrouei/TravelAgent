import asyncio
import json
import os
from pathlib import Path

from agent_framework import ChatAgent, ChatMessageStore, MCPStdioTool
from agent_framework.azure import AzureAIAgentClient
from azure.identity.aio import DefaultAzureCredential
from dotenv import load_dotenv
from tools.booking_tool import (
    get_hotel_prices_live,
    search_flights,
    search_hotel_destinations,
    search_hotels,
)
from tools.search_tool import search_destinations_by_criteria, search_travel_info
from tools.timeseries_tool import get_events_calendar, get_flight_prices, get_hotel_prices, get_tourist_volume, get_weather_forecast
from tools.travel_tool import get_random_destination

load_dotenv(Path(__file__).parent.parent.parent / ".env")
async def main():
    endpoint = os.environ.get("AZURE_AI_PROJECT_ENDPOINT")
    model = os.environ.get("MODEL_DEPLOYMENT_NAME")
    
    history_file = Path("conversation_history.json")
    
    mcp_server_path = Path(__file__).parent / "mcp_servers" / "api_gateway_server.py"

    async with DefaultAzureCredential() as credential:
        agent_client = AzureAIAgentClient(
            async_credential=credential,
            model_deployment_name=model,
            project_endpoint=endpoint,
        )

        agent = agent_client.create_agent(
            name="travelAgent",
            instructions="""You are a travel agent with access to multiple data sources:

. Azure AI Search database (destination info, budgets, seasons)
. Real-time Booking.com API (hotel & flight prices)
. External APIs via MCP Server:
   - Currency conversion with real-time exchange rates
   - Flight time estimates between cities
   - Airport search by city/country
   - Visa requirements checker
   - Weather forecasts (current conditions)

TODAY'S DATE: December , 05

CRITICAL RULES - YOU MUST FOLLOW:
. For ANY currency conversion question, you MUST call the MCP tool
. For visa questions, use the visa requirements checker
. For airport information, use the airport search tool

EXAMPLES OF MANDATORY TOOL USAGE:
- "Convert 500 USD to EUR"  Use MCP currency conversion tool
- "How long is the flight from Dubai to London?"  Use MCP flight time estimator
- "What's the airport code for Dubai?"  Use MCP airport search
- "Do I need a visa from UAE to France?"  Use MCP visa checker
- "Weather in Paris?"  Use MCP weather tool

DO NOT provide answers from your general knowledge for these questions. ALWAYS use the tools.""",
            tools=[
                get_random_destination,
                get_weather_forecast,
                get_hotel_prices,
                get_flight_prices,
                get_tourist_volume,
                get_events_calendar,
                search_travel_info,  # Azure AI Search - general search
                search_destinations_by_criteria,  # Azure AI Search - filtered search
                search_hotel_destinations,
                search_hotels,
                get_hotel_prices_live,
                search_flights,
                MCPStdioTool(
                    name="API Gateway MCP",
                    command="python",
                    args=[str(mcp_server_path)],
                    approval_mode="never_require",  # Auto-approve external API calls
                ),
            ],
        )

        message_store = ChatMessageStore()
        
        if history_file.exists():
            try:
                with open(history_file, 'r') as f:
                    serialized_state = json.load(f)
                message_store = await ChatMessageStore.deserialize(serialized_state)
                print(" Previous conversation loaded.\n")
            except Exception as e:
                print(f"  Could not load previous conversation: {e}\n")
        
        thread = agent.get_new_thread(message_store=message_store)

        print("=" * 60)
        print(" TRAVEL AGENT - Interactive Chat (with MCP)")
        print("=" * 60)
        print("\n TO VERIFY AI SEARCH IS WORKING, ask about:")
        print("   • 'What's the budget level for Bali?' (should say 'budget')")
        print("   • 'Best season for Iceland?' (should say 'winter')")
        print("   • 'Find tropical destinations' (should find Bali)")
        print("\n TO TEST BOOKING.COM API (real prices), ask:")
        print("   • 'Find hotels in Dubai'")
        print("   • 'Show me hotels in Paris for next week'")
        print("   • 'What are hotel prices in Tokyo?'")
        print("\n TO TEST MCP EXTERNAL APIs, ask:")
        print("   • 'What airports are in Dubai?'  (Airport Search)")
        print("   • 'Do I need a visa from UAE to France?'  (Visa Requirements)")
        print("   • 'How long is the flight from Dubai to London?'  (Flight Time)")
        print("   • 'Convert 000 USD to EUR'  (Currency)")
        print("   • 'Weather in Tokyo'  (Weather)")
        print("\nType 'exit' or 'quit' to end the conversation.\n")
        print("=" * 60 + "\n")

        while True:
            try:
                user_input = input("You: ").strip()

                if user_input.lower() in ["exit", "quit", "bye", "goodbye"]:
                    print("\n Thank you for using Travel Agent! Safe travels!\n")
                    break

                if not user_input:
                    continue

                print("\n Agent: ", end="", flush=True)

                response = await agent.run(user_input, thread=thread)

                print(f"{response}\n")
                
                try:
                    serialized_state = await message_store.serialize()
                    with open(history_file, 'w') as f:
                        json.dump(serialized_state, f, indent=)
                except Exception as e:
                    print(f"  Could not save conversation: {e}")

            except KeyboardInterrupt:
                print("\n\n Chat interrupted. Goodbye!\n")
                try:
                    serialized_state = await message_store.serialize()
                    with open(history_file, 'w') as f:
                        json.dump(serialized_state, f, indent=)
                    print(" Conversation saved.\n")
                except Exception as e:
                    print(f"  Could not save conversation: {e}\n")
                break
            except Exception as e:
                print(f"\n Error: {str(e)}\n")
                continue
if __name__ == "__main__":
    asyncio.run(main())
"""
observations:
"""
