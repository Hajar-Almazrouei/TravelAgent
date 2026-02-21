# AI Travel Agent — Trip Planning with Real-Time Data

An agent built on **Azure AI Agent Framework**, **Azure OpenAI (GPT-4)**, and **MCP**.  
It combines real-time hotel/flight pricing, semantic destination search, and weather forecasts into a single conversational interface.

---

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

> View the full interactive diagram: [`travelagent_v3.drawio`](travelagent_v3.drawio) (open with [draw.io](https://app.diagrams.net))

```
┌─────────────────────────────────────────────────────┐
│                  User Interfaces                     │
│         CLI Chat  ·  DevUI  ·  REST API              │
└────────────────────────┬────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────┐
│          Travel Agent  (Azure OpenAI GPT-4)          │
│    Intent understanding · Tool orchestration         │
│    Thread-based memory  · Response formatting        │
└───┬──────────┬──────────┬──────────┬────────────────┘
    │          │          │          │
┌───▼───┐ ┌───▼───┐ ┌───▼────┐ ┌───▼──────────┐
│Azure  │ │Booking│ │Weather │ │ MCP Server   │
│AI     │ │.com   │ │(Open-  │ │  · Currency  │
│Search │ │API    │ │ Meteo) │ │  · Airports  │
│(600+) │ │       │ │        │ │  · Visa info │
└───────┘ └───────┘ └────────┘ └──────────────┘
```

---

## Project Structure

```
TravelAgent/
├── chat_agent.py                  # Main agent with MCP tool support
├── mcp_servers/
│   ├── api_gateway_server.py      # MCP server (currency, flights, airports)
│   ├── airport_tool.py            # Airport search (Azure AI Search + fallback DB)
│   └── create_airports_index.py   # Index builder for airport data
├── api/
│   └── main.py                    # FastAPI REST backend
└── tools/
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
   poetry install
   poetry shell
   ```

2. **Configure environment variables** in a `.env` file at the project root:

   | Variable | Description |
   |----------|-------------|
   | `AZURE_AI_PROJECT_ENDPOINT` | Azure AI project endpoint |
   | `MODEL_DEPLOYMENT_NAME` | Azure OpenAI model deployment (e.g. `gpt-4`) |
   | `AZURE_AI_SEARCH_ENDPOINT` | Azure AI Search endpoint URL |
   | `RAPIDAPI_KEY` | RapidAPI key for Booking.com |

3. **Run the agent:**

   ```bash
   # CLI chat
   python src/TravelAgent/chat_agent.py

   # REST API
   uvicorn src.TravelAgent.api.main:app --reload
   ```

### Development

```bash
pytest              # Run tests
ruff format .       # Format code
ruff check .        # Lint
mypy src/           # Type check
```