# AI Travel Agent —  Trip Planning with Real-Time Data

An agent built on **Azure AI Agent Framework**, **Azure OpenAI (GPT-4)**, and **MCP**. It combines real-time hotel/flight pricing, semantic destination search, and weather forecasts into a single conversational interface.

![Architecture Diagram](travelagent_v3.drawio)

## What This Project Does

The agent acts as a smart travel assistant that can:

- **Search 600+ destinations** via Azure AI Search with semantic vector matching
- **Find real-time hotel prices & availability** through Booking.com API (RapidAPI)
- **Look up flights** with live pricing data
- **Check weather forecasts** for any destination
- **Convert currencies**, estimate flight times, search airports, and check visa requirements via MCP tools
- **Maintain conversation context** across multi-turn dialogues using threads
---

## Architecture

See the full architecture diagram: [travelagent_v3.drawio](travelagent_v3.drawio)
---

## Project Structure

```
TravelAgent/                       # Travel Agent with MCP integration
├── chat_agent.py                  # Agent with MCP tool support
├── mcp_servers/
│   ├── api_gateway_server.py      # MCP server (currency, flights, airports)
│   ├── airport_tool.py            # Airport search (Azure AI Search + fallback DB)
│   └── create_airports_index.py   # Index builder for airport data
├── api/main.py                    # FastAPI REST backend
└── tools/                         # Agent tool implementations
    ├── search_tool.py             # Azure AI Search integration
    ├── booking_tool.py            # Booking.com API (hotels, flights)
    └── travel_tool.py             # Utility tools
```

---

## Getting Started

### Prerequisites

- **Python 3.12+**
- **Azure subscription** with Azure OpenAI and Azure AI Search provisioned
- **VS Code** with the Dev Container extension (recommended) or Docker Desktop
- **RapidAPI key** for Booking.com API (for hotel/flight tools)

### Setup

1. **Open in Dev Container** (recommended) — VS Code will detect `.devcontainer/` and offer to reopen:

   ```bash
   # Or install dependencies manually:
   poetry install
   poetry shell
   ```

2. **Configure environment variables:**

   | Variable | Description |
   |----------|-------------|
   | `PROJECT_CONNECTION_STRING` | Azure AI project connection string |
   | `MODEL_DEPLOYMENT_NAME` | Azure OpenAI model deployment (e.g. `gpt-4`) |
   | `AZURE_AI_SEARCH_ENDPOINT` | Azure AI Search endpoint URL |
   | `RAPIDAPI_KEY` | RapidAPI key for Booking.com |

3. **Run the agent:**

   ```bash
   # CLI chat
   python src/agents_playground/chat_agent.py

   # DevUI (browser at http://127.0.0.1:8090)
   python src/agents_playground/devui_travel_agent.py

   # REST API
   uvicorn src.agents_playground.api.main:app --reload
   ```

### Development Workflow

```bash
pytest              # Run tests with coverage
ruff format .       # Format code
ruff check .        # Lint
mypy src/           # Type check
make test           # Run all checks
```