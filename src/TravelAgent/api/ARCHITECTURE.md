# FastAPI Backend Architecture - Step by Step

## 🏗️ Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                         FastAPI Server                           │
│                      (http://localhost:8000)                     │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ├── Startup
                     │   └── Initialize Agent + Tools once
                     │
                     ├── Storage (In-Memory)
                     │   ├── conversations: { conv_id → thread }
                     │   └── messages: { conv_id → [msg1, msg2...] }
                     │
                     └── Endpoints
                         ├── GET  /
                         ├── POST /chat
                         ├── GET  /conversations
                         ├── GET  /conversations/{id}/messages
                         ├── DELETE /conversations/{id}
                         ├── GET  /tools
                         └── GET  /stats
```

---

## 📊 Data Flow for POST /chat

```
┌─────────┐     1. HTTP POST       ┌──────────────┐
│ Client  │ ──────────────────────> │  FastAPI     │
│ (curl,  │  {"message": "Hello"}  │  /chat       │
│  app)   │                         │  endpoint    │
└─────────┘                         └──────┬───────┘
                                           │
                                    2. Check if conversation exists
                                           │
                            ┌──────────────┴──────────────┐
                            │                             │
                      NEW CONVERSATION             EXISTING CONVERSATION
                            │                             │
                    3a. Create new thread          3b. Get existing thread
                    conversations[uuid] = {        thread = conversations[uuid]["thread"]
                      thread: agent.get_new_thread(),
                      created_at: "2025-11-25..."
                    }
                            │                             │
                            └──────────────┬──────────────┘
                                           │
                              4. Store user message
                              messages[conv_id].append({
                                "role": "user",
                                "content": "Hello",
                                "timestamp": "..."
                              })
                                           │
                              5. Run agent with thread
                              response = await agent.run(
                                user_message,
                                thread=thread
                              )
                                           │
                    ┌──────────────────────┴────────────────────────┐
                    │        Agent decides which tools to use       │
                    ├───────────────────────────────────────────────┤
                    │  Tool 1: search_travel_info("Dubai")          │
                    │  Tool 2: get_weather_forecast("Dubai", 5)     │
                    │  Tool 3: get_hotel_prices("Dubai")            │
                    └──────────────────────┬────────────────────────┘
                                           │
                              6. Store agent response
                              messages[conv_id].append({
                                "role": "assistant",
                                "content": "Dubai is...",
                                "timestamp": "..."
                              })
                                           │
                              7. Return to client
                              ↓
┌─────────┐     HTTP Response        ┌──────────────┐
│ Client  │ <──────────────────────── │  FastAPI     │
│         │  {                        │              │
│         │    "conversation_id": "...",              │
│         │    "response": "Dubai is...",             │
│         │    "timestamp": "..."                     │
│         │  }                                        │
└─────────┘                         └──────────────┘
```

---

## 🔧 What Tools Should Appear?

### **Current Tools in Your API:**

| Tool Name | Type | Status | What It Does |
|-----------|------|--------|--------------|
| `get_random_destination` | Utility | ✅ Working | Returns random destination from list |
| `get_weather_forecast` | API (Open-Meteo) | ✅ Working | Real weather data for location |
| `get_hotel_prices` | Mock | ⚠️ Fallback | Returns mock hotel prices (fallback) |
| `get_flight_prices` | Mock | ⚠️ Fallback | Returns mock flight prices (fallback) |
| `get_tourist_volume` | Mock | ⚠️ Placeholder | Returns fake crowd data |
| `get_events_calendar` | Mock | ⚠️ Placeholder | Returns fake events |
| `search_travel_info` | Azure AI Search | ✅ Working | Searches your travel-index |
| `search_destinations_by_criteria` | Azure AI Search | ✅ Working | Filtered search by budget/climate/season |
| `search_hotel_destinations` | Booking.com API | ✅ Working | Search destinations for hotel lookup |
| `search_hotels` | Booking.com API | ✅ Working | Get real-time hotel listings with prices |
| `get_hotel_prices_live` | Booking.com API | ✅ Working | One-step hotel search with live prices |
| `search_flights` | Booking.com API | ⚠️ Premium | Flight search (requires premium API tier) |

**GET /tools endpoint shows all 12 tools**

---

## 🔑 Booking.com API Setup (RapidAPI)

To enable real-time hotel data from Booking.com:

### **1. Get API Key:**
1. Create account at [RapidAPI](https://rapidapi.com)
2. Subscribe to [Booking.com API](https://rapidapi.com/tipsters/api/booking-com)
3. Copy your API key

### **2. Configure Environment:**
Add to your `.env` file:
```env
RAPIDAPI_KEY=your_rapidapi_key_here
RAPIDAPI_HOST=booking-com15.p.rapidapi.com
```

### **3. API Endpoints Used:**
| Endpoint | Purpose |
|----------|---------|
| `/api/v1/hotels/searchDestination` | Find destination IDs for cities |
| `/api/v1/hotels/searchHotels` | Get hotel listings with prices |
| `/api/v1/flights/searchFlights` | Search flights (premium tier) |

### **4. Usage Examples:**
```
User: "Find hotels in Paris for next week"
→ Agent calls search_hotel_destinations("Paris") to get destination ID
→ Agent calls search_hotels(dest_id, checkin, checkout) to get prices

User: "How much are hotels in Tokyo?"  
→ Agent calls get_hotel_prices_live("Tokyo") (combines both steps)
```

**Note:** Flight search requires a premium RapidAPI subscription. The hotel APIs work with the free tier (with rate limits).

---

## 🎯 What Should You Expose in Your API?

### **✅ Already Exposed (Good!):**

1. **POST /chat** - Main interaction
2. **GET /conversations** - List all conversations
3. **GET /conversations/{id}/messages** - Message history
4. **DELETE /conversations/{id}** - Delete conversation
5. **GET /tools** - List available tools
6. **GET /stats** - Usage statistics

### **🚀 Recommended Additions:**

| Endpoint | Purpose | Priority |
|----------|---------|----------|
| `POST /conversations/new` | Explicitly create new conversation | Medium |
| `GET /tools/{tool_name}` | Get details about specific tool | Low |
| `POST /tools/{tool_name}/invoke` | Directly call a tool without agent | High |
| `GET /conversations/{id}/thread_id` | Get Azure thread ID for conversation | Medium |
| `POST /conversations/{id}/clear` | Clear message history but keep conversation | Low |
| `GET /health` | Detailed health check (DB, Azure, etc.) | High |
| `POST /chat/stream` | Stream agent responses (WebSocket) | High |
| `GET /conversations/{id}/summary` | AI-generated conversation summary | Low |

---

## 📝 Swagger UI - What Users See

When you open **http://localhost:8000/docs**, users see:

### **Interactive Documentation:**

```
Travel Agent API
v1.0.0

Endpoints:

▼ default
  GET  /              Health check
  POST /chat          Send a message to the agent
  GET  /conversations List all conversations
  GET  /conversations/{conversation_id}/messages  Get message history
  DELETE /conversations/{conversation_id}  Delete conversation
  GET  /tools         List available tools
  GET  /stats         Get usage statistics

Schemas:
  - ChatRequest
  - ChatResponse
  - ConversationInfo
  - ToolInfo
  - MessageHistory
```

### **Example: Trying POST /chat in Swagger:**

```json
// Request Body (user fills this in Swagger UI)
{
  "message": "What's the weather in Paris?",
  "conversation_id": "optional-uuid"
}

// Response (Swagger shows this)
{
  "conversation_id": "abc-123-def",
  "message": "What's the weather in Paris?",
  "response": "The weather in Paris for the next 5 days...",
  "timestamp": "2025-11-25T10:30:00",
  "tools_used": []
}
```

---

## 🎨 Current Swagger UI Status

**What works now:**
- ✅ All 7 endpoints fully functional
- ✅ Request/Response schemas defined
- ✅ Try it out button works
- ✅ Example values auto-populated
- ✅ Error responses documented (500, 404)

**What's missing:**
- ⚠️ `tools_used` field is empty (not tracking which tools agent calls)
- ⚠️ No endpoint to directly invoke a tool
- ⚠️ No streaming support
- ⚠️ No authentication/authorization

---

## 🔍 Understanding the Storage

### **Example State After 2 Conversations:**

```python
# conversations dictionary
{
  "uuid-aaa-111": {
    "thread": <AgentThread object>,
    "created_at": "2025-11-25T10:00:00",
    "thread_id": "thread_abc123"
  },
  "uuid-bbb-222": {
    "thread": <AgentThread object>,
    "created_at": "2025-11-25T10:15:00",
    "thread_id": "thread_xyz789"
  }
}

# messages dictionary
{
  "uuid-aaa-111": [
    {"role": "user", "content": "Hello", "timestamp": "2025-11-25T10:00:01"},
    {"role": "assistant", "content": "Hi! How can I help?", "timestamp": "2025-11-25T10:00:02"},
    {"role": "user", "content": "Weather in Paris?", "timestamp": "2025-11-25T10:01:00"},
    {"role": "assistant", "content": "The weather...", "timestamp": "2025-11-25T10:01:05"}
  ],
  "uuid-bbb-222": [
    {"role": "user", "content": "Find tropical places", "timestamp": "2025-11-25T10:15:01"},
    {"role": "assistant", "content": "I found Bali...", "timestamp": "2025-11-25T10:15:03"}
  ]
}
```

---

## 🚦 What Happens When Server Restarts?

**⚠️ Important:** 
```
Server Restarts → All conversations LOST (in-memory storage)
```

**For Production:**
- Replace `conversations` and `messages` dicts with database (PostgreSQL, MongoDB)
- Persist thread IDs to resume conversations
- Add user authentication

---

## 🎯 Summary

**Your API is a REST wrapper around your Agent Framework:**

1. **Startup**: Initialize agent once with all tools
2. **POST /chat**: Create thread, run agent, store messages
3. **Storage**: Keep everything in memory (for now)
4. **Tools**: Agent automatically picks from 8 available tools
5. **Swagger**: Auto-generated interactive docs at /docs

**Ready to test?** Open http://localhost:8000/docs and try the POST /chat endpoint!

Would you like me to:
1. Add tool invocation tracking (show which tools were used)?
2. Add direct tool invocation endpoint?
3. Add streaming support?
4. Add database persistence?
