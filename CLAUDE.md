# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

A Python FastAPI backend service for managing bowling shoe rentals with an **agentic AI chatbot** that orchestrates tools for customer management, rental processing, and discount calculations. The system supports multiple LLM providers (Anthropic, OpenAI, Groq) and includes a React/TypeScript frontend with WebSocket-based streaming.

## Architecture

```
┌─────────────────┐     ┌──────────────────┐     ┌────────────┐
│  React/Vite     │────▶│   FastAPI        │────▶│  Supabase  │
│  Frontend (TS)  │◀────│   + WebSocket    │◀────│            │
└─────────────────┘     └────────┬─────────┘     └────────────┘
                                 │
                        ┌────────▼─────────┐
                        │   Agent Engine   │
                        │  (orchestrator)  │
                        └────────┬─────────┘
                                 │
              ┌──────────────────┼──────────────────┐
              ▼                  ▼                  ▼
      ┌──────────────┐  ┌──────────────┐  ┌──────────────┐
      │ LLM Provider │  │    Tools     │  │Tool Registry │
      │ (abstract)   │  │ (functions)  │  │              │
      └──────────────┘  └──────────────┘  └──────────────┘
```

## File Structure

```
app/
├── main.py                 # FastAPI app, CORS, routers
├── config.py               # Environment configuration
├── database.py             # Supabase CRUD operations
├── endpoints/
│   ├── customers.py        # Customer REST API (/customers/*)
│   ├── rentals.py          # Rental REST API with tool-based discounts
│   └── chat.py             # WebSocket chat endpoint (/chat/ws/{session_id})
├── agent/
│   ├── engine.py           # Agent orchestration loop
│   ├── context.py          # Conversation history management
│   └── prompts.py          # System prompts
├── llm/
│   ├── base.py             # Abstract LLM provider interface
│   ├── anthropic_provider.py
│   ├── openai_provider.py
│   ├── groq_provider.py
│   └── factory.py          # Provider factory
├── tools/
│   ├── base.py             # Tool interface
│   ├── registry.py         # Tool registration/execution
│   ├── discount_tools.py   # Age, disability, medical discounts
│   ├── customer_tools.py   # Customer CRUD tools
│   ├── rental_tools.py     # Rental management tools
│   └── info_tools.py       # Pricing/service info tools
└── schemas/
    ├── chat.py             # WebSocket message schemas
    └── tools.py            # Tool I/O schemas

frontend/                   # React/Vite/TypeScript chat UI
├── src/
│   ├── components/         # Chat, Message, ToolCallDisplay components
│   ├── hooks/useWebSocket.ts
│   ├── types/chat.ts
│   └── styles/chat.css
├── package.json
└── vite.config.ts
```

## Development Commands

```bash
# Backend only (with local Python environment)
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# Frontend only (development)
cd frontend
npm install
npm run dev

# Full stack with Docker
docker-compose up --build

# API documentation
# http://localhost:8000/docs (Swagger UI)
# http://localhost:8000/redoc
```

## Available Tools (Agent)

| Tool | Description |
|------|-------------|
| `calculate_age_discount` | Calculate age-based discount (0-12: 20%, 13-18: 10%, 65+: 15%) |
| `calculate_disability_discount` | Calculate disability discount (25%) |
| `calculate_medical_discount` | Calculate medical condition discounts (10% each, stacks) |
| `get_best_discount` | Get highest applicable discount for customer |
| `lookup_customer` | Find customer by name or ID |
| `create_customer` | Create new customer record |
| `update_customer` | Update customer information |
| `list_customers` | List/filter customers |
| `create_rental` | Create rental with auto-discount |
| `get_rental_history` | Get customer rental history |
| `cancel_rental` | Cancel a rental |
| `get_pricing_info` | Get pricing and discount policies |
| `get_service_info` | Get service information |

## Key Technologies

- **FastAPI 0.112.0** - Web framework with WebSocket support
- **Supabase 2.6.0** - PostgreSQL cloud database
- **Anthropic/OpenAI/Groq SDKs** - LLM providers
- **React 18** - Frontend UI
- **Vite 5** - Frontend build tool
- **TypeScript 5** - Type-safe frontend

## Database Schema

Two tables in Supabase (defined in `script.sql`):
- **customers**: id, name, age, contact_info, is_disabled, medical_conditions
- **rentals**: id, customer_id (FK), rental_date, shoe_size, rental_fee, discount, total_fee

## Environment Variables

```bash
# Required
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_API_KEY=your-supabase-key

# LLM Configuration
LLM_PROVIDER=anthropic  # or "openai" or "groq"
ANTHROPIC_API_KEY=your-key  # if using anthropic
OPENAI_API_KEY=your-key     # if using openai
GROQ_API_KEY=your-key       # if using groq

# Optional
LLM_MODEL=claude-sonnet-4-20250514  # override default model
CORS_ORIGINS=http://localhost:5173  # comma-separated
```

## WebSocket Protocol

```
Client → Server:
  { "type": "message", "content": "I want to rent shoes" }

Server → Client:
  { "type": "stream_start" }
  { "type": "text_delta", "content": "Hello" }
  { "type": "tool_call_start", "tool_call_id": "...", "tool": "lookup_customer", "args": {...} }
  { "type": "tool_call_result", "tool_call_id": "...", "tool": "lookup_customer", "result": {...} }
  { "type": "stream_end" }
```

## Testing

No test suite currently exists. Tests would need to be added with pytest.

## Notes

- Discount calculations are deterministic (tools, not LLM math)
- REST API (`/customers/*`, `/rentals/*`) still works independently
- Chat uses WebSocket at `/chat/ws/{session_id}`
- Frontend auto-reconnects on WebSocket disconnect
- The typo `clinet` in `app/database.py:66` still exists but doesn't affect functionality
