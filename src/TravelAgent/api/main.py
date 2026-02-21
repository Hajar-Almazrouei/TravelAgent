"""
FastAPI Backend for Travel Agent
Provides REST API endpoints for:
- Managing agent conversations
- Viewing message history
- Listing available tools
- Agent chat endpoint
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import asyncio
import os
from dotenv import load_dotenv
from datetime import datetime
import uuid

from agent_framework import ChatAgent
from agent_framework.azure import AzureAIAgentClient
from azure.identity.aio import DefaultAzureCredential

import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from tools.travel_tool import get_random_destination
from tools.timeseries_tool import (
    get_weather_forecast,
    get_hotel_prices,
    get_flight_prices,
    get_tourist_volume,
    get_events_calendar
)
from tools.search_tool import (
    search_travel_info,
    search_destinations_by_criteria
)
from tools.booking_tool import (
    search_hotel_destinations,
    search_hotels,
    get_hotel_prices_live,
    search_flights,
)

load_dotenv()

app = FastAPI(
    title="Travel Agent API",
    description="REST API for AI Travel Agent with tools and conversation management",
    version=".0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

conversations: Dict[str, Dict[str, Any]] = {}
messages: Dict[str, List[Dict[str, Any]]] = {}

agent = None
agent_client = None
credential = None

class ChatRequest(BaseModel):
    message: str
    conversation_id: Optional[str] = None

class ChatResponse(BaseModel):
    conversation_id: str
    message: str
    response: str
    timestamp: str
    tools_used: List[str] = []

class ConversationInfo(BaseModel):
    conversation_id: str
    created_at: str
    message_count: int
    last_message: Optional[str] = None

class ToolInfo(BaseModel):
    name: str
    description: str
    type: str

class MessageHistory(BaseModel):
    conversation_id: str
    messages: List[Dict[str, Any]]

@app.on_event("startup")
async def startup_event():
    global agent, agent_client, credential
    
    endpoint = os.environ.get("AZURE_AI_PROJECT_ENDPOINT")
    model = os.environ.get("MODEL_DEPLOYMENT_NAME")
    
    credential = DefaultAzureCredential()
    agent_client = AzureAIAgentClient(
        async_credential=credential,
        model_deployment_name=model,
        project_endpoint=endpoint,
    )
    
    agent = ChatAgent(
        chat_client=agent_client,
        name="travelAgent",
        instructions="""You are a travel agent with access to multiple tools and a travel database.
        Use tools to provide accurate, real-time information to users.
        
        For hotel searches, prefer using the Booking.com API tools (search_hotel_destinations, 
        search_hotels, get_hotel_prices_live) for real-time pricing data instead of mock data.
        
        Workflow for hotel searches:
        . Use search_hotel_destinations to find the destination ID
        . Use search_hotels with the destination ID to get hotel listings with prices
        OR use get_hotel_prices_live which combines both steps.""",
        tools=[
            get_random_destination,
            get_weather_forecast,
            get_hotel_prices,  # Mock fallback
            get_flight_prices,  # Mock fallback  
            get_tourist_volume,
            get_events_calendar,
            search_travel_info,
            search_destinations_by_criteria,
            search_hotel_destinations,
            search_hotels,
            get_hotel_prices_live,
            search_flights,
        ]
    )
    
    print(" Travel Agent API started successfully!")

@app.on_event("shutdown")
async def shutdown_event():
    global credential
    if credential:
        await credential.close()
@app.get("/")
async def root():
    """API health check"""
    return {
        "status": "running",
        "service": "Travel Agent API",
        "version": ".0.0",
        "endpoints": {
            "chat": "/chat",
            "conversations": "/conversations",
            "messages": "/conversations/{conversation_id}/messages",
            "tools": "/tools"
        }
    }

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Send a message to the agent and get a response
    """
    global agent, conversations, messages
    
    conversation_id = request.conversation_id or str(uuid.uuid4())
    
    if conversation_id not in conversations:
        thread = agent.get_new_thread()
        conversations[conversation_id] = {
            "thread": thread,
            "created_at": datetime.now().isoformat(),
            "thread_id": thread.id if hasattr(thread, 'id') else None
        }
        messages[conversation_id] = []
    
    thread = conversations[conversation_id]["thread"]
    
    user_message = {
        "role": "user",
        "content": request.message,
        "timestamp": datetime.now().isoformat()
    }
    messages[conversation_id].append(user_message)
    
    try:
        response = await agent.run(request.message, thread=thread)
        
        agent_message = {
            "role": "assistant",
            "content": str(response),
            "timestamp": datetime.now().isoformat()
        }
        messages[conversation_id].append(agent_message)
        
        return ChatResponse(
            conversation_id=conversation_id,
            message=request.message,
            response=str(response),
            timestamp=datetime.now().isoformat(),
            tools_used=[]  # TODO: Extract from agent response
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/conversations", response_model=List[ConversationInfo])
async def list_conversations():
    """
    Get list of all conversations
    """
    result = []
    for conv_id, conv_data in conversations.items():
        conv_messages = messages.get(conv_id, [])
        last_msg = conv_messages[-]["content"] if conv_messages else None
        
        result.append(ConversationInfo(
            conversation_id=conv_id,
            created_at=conv_data["created_at"],
            message_count=len(conv_messages),
            last_message=last_msg
        ))
    
    return result

@app.get("/conversations/{conversation_id}/messages", response_model=MessageHistory)
async def get_conversation_messages(conversation_id: str):
    """
    Get full message history for a conversation
    """
    if conversation_id not in conversations:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    return MessageHistory(
        conversation_id=conversation_id,
        messages=messages.get(conversation_id, [])
    )

@app.delete("/conversations/{conversation_id}")
async def delete_conversation(conversation_id: str):
    """
    Delete a conversation and its messages
    """
    if conversation_id not in conversations:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    del conversations[conversation_id]
    if conversation_id in messages:
        del messages[conversation_id]
    
    return {"status": "deleted", "conversation_id": conversation_id}

@app.get("/tools", response_model=List[ToolInfo])
async def list_tools():
    """
    Get list of all available tools
    """
    tools_list = [
        ToolInfo(
            name="get_random_destination",
            description="Suggests a random travel destination from curated list",
            type="utility"
        ),
        ToolInfo(
            name="get_weather_forecast",
            description="Get real-time weather forecast using Open-Meteo API",
            type="api"
        ),
        ToolInfo(
            name="get_hotel_prices",
            description="Get hotel price trends and estimates (mock fallback)",
            type="mock"
        ),
        ToolInfo(
            name="get_flight_prices",
            description="Get flight price estimates (mock fallback)",
            type="mock"
        ),
        ToolInfo(
            name="get_tourist_volume",
            description="Get crowd levels and tourist traffic data",
            type="mock"
        ),
        ToolInfo(
            name="get_events_calendar",
            description="Get local events and activities",
            type="mock"
        ),
        ToolInfo(
            name="search_travel_info",
            description="Search Azure AI Search travel database",
            type="azure_ai_search"
        ),
        ToolInfo(
            name="search_destinations_by_criteria",
            description="Filter destinations by climate, budget, season using Azure AI Search",
            type="azure_ai_search"
        ),
        ToolInfo(
            name="search_hotel_destinations",
            description="Search for hotel destinations on Booking.com by city name",
            type="booking_api"
        ),
        ToolInfo(
            name="search_hotels",
            description="Get real-time hotel listings with prices from Booking.com",
            type="booking_api"
        ),
        ToolInfo(
            name="get_hotel_prices_live",
            description="Get real-time hotel prices from Booking.com (combines destination + hotel search)",
            type="booking_api"
        ),
        ToolInfo(
            name="search_flights",
            description="Search for flight prices using Booking.com API",
            type="booking_api"
        ),
    ]
    
    return tools_list

@app.get("/stats")
async def get_stats():
    """
    Get API usage statistics
    """
    total_messages = sum(len(msgs) for msgs in messages.values())
    
    return {
        "total_conversations": len(conversations),
        "total_messages": total_messages,
        "active_conversations": len([c for c in conversations if messages.get(c)]),
        "available_tools":   # Updated to include Booking.com tools
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
