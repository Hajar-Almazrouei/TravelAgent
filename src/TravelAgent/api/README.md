# Travel Agent REST API

Backend API for managing AI Travel Agent conversations, tools, and message history.

## Features

- ✅ Chat with AI agent via REST API
- ✅ Manage multiple conversations
- ✅ View message history
- ✅ List available tools
- ✅ Get usage statistics
- ✅ CORS enabled for frontend integration

## Quick Start

### 1. Start the API Server

```bash
cd src/agents_playground
uv run uvicorn api.main:app --reload --port 8000
```

### 2. Access API Documentation

Open in browser:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## API Endpoints

### Health Check
```bash
GET /
```

### Chat with Agent
```bash
POST /chat
Content-Type: application/json

{
  "message": "What's the weather in Paris?",
  "conversation_id": "optional-conversation-id"
}
```

### List Conversations
```bash
GET /conversations
```

### Get Message History
```bash
GET /conversations/{conversation_id}/messages
```

### Delete Conversation
```bash
DELETE /conversations/{conversation_id}
```

### List Available Tools
```bash
GET /tools
```

### Get Statistics
```bash
GET /stats
```

## Example Usage

### Using curl

```bash
# Start a new conversation
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Suggest a random destination"}'

# Continue conversation
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What is the weather there?",
    "conversation_id": "YOUR_CONVERSATION_ID"
  }'

# List all conversations
curl http://localhost:8000/conversations

# Get message history
curl http://localhost:8000/conversations/YOUR_CONVERSATION_ID/messages

# List tools
curl http://localhost:8000/tools

# Get stats
curl http://localhost:8000/stats
```

### Using Python requests

```python
import requests

# Start conversation
response = requests.post(
    "http://localhost:8000/chat",
    json={"message": "Tell me about Dubai"}
)
data = response.json()
print(f"Response: {data['response']}")
print(f"Conversation ID: {data['conversation_id']}")

# Continue conversation
response = requests.post(
    "http://localhost:8000/chat",
    json={
        "message": "What's the weather forecast?",
        "conversation_id": data['conversation_id']
    }
)
print(response.json()['response'])
```

### Using JavaScript fetch

```javascript
// Start conversation
const response = await fetch('http://localhost:8000/chat', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ message: 'Find tropical destinations' })
});
const data = await response.json();
console.log('Response:', data.response);
console.log('Conversation ID:', data.conversation_id);

// Get message history
const history = await fetch(`http://localhost:8000/conversations/${data.conversation_id}/messages`);
const messages = await history.json();
console.log('Messages:', messages);
```

## Response Format

### Chat Response
```json
{
  "conversation_id": "uuid-string",
  "message": "user message",
  "response": "agent response",
  "timestamp": "2025-11-24T12:00:00",
  "tools_used": []
}
```

### Message History
```json
{
  "conversation_id": "uuid-string",
  "messages": [
    {
      "role": "user",
      "content": "Hello",
      "timestamp": "2025-11-24T12:00:00"
    },
    {
      "role": "assistant",
      "content": "Hi! How can I help?",
      "timestamp": "2025-11-24T12:00:01"
    }
  ]
}
```

### Tools List
```json
[
  {
    "name": "get_weather_forecast",
    "description": "Get real-time weather forecast using Open-Meteo API",
    "type": "api"
  },
  {
    "name": "search_travel_info",
    "description": "Search Azure AI Search travel database",
    "type": "azure_ai_search"
  }
]
```

## Storage

Currently uses **in-memory storage** (conversations and messages stored in RAM).

### Production Considerations:
- Replace with database (PostgreSQL, MongoDB, etc.)
- Add user authentication
- Implement rate limiting
- Add conversation persistence
- Configure CORS for specific origins

## Architecture

```
api/
├── main.py          # FastAPI application
└── README.md        # This file

Flow:
1. Client sends POST to /chat
2. API creates/retrieves conversation thread
3. Agent processes message with tools
4. Response stored in message history
5. Client receives response
```

## Environment Variables

Make sure `.env` is configured:
```
AZURE_AI_PROJECT_ENDPOINT=your_endpoint
MODEL_DEPLOYMENT_NAME=gpt-4o
AZURE_SEARCH_ENDPOINT=your_search_endpoint
AZURE_SEARCH_INDEX_NAME=travel-index
```

## Next Steps

- [ ] Add database for persistence
- [ ] Add user authentication (JWT)
- [ ] Add WebSocket support for streaming responses
- [ ] Add rate limiting
- [ ] Add logging and monitoring
- [ ] Deploy to Azure App Service or Container Apps

## Testing

```bash
# Test health endpoint
curl http://localhost:8000/

# Test interactive docs
# Open http://localhost:8000/docs
# Try out endpoints in Swagger UI
```

## Troubleshooting

**Port already in use:**
```bash
# Use different port
uvicorn api.main:app --port 8001
```

**Azure authentication errors:**
```bash
# Make sure you're logged in
az login
```

**Module not found:**
```bash
# Make sure you're in the right directory
cd src/agents_playground
# And FastAPI is installed
uv pip list | grep fastapi
```
