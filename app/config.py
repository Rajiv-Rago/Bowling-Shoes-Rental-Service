from dotenv import load_dotenv
import os

load_dotenv()

# Database configuration
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_API_KEY = os.getenv("SUPABASE_API_KEY")

# Legacy LLM key (for backward compatibility with Lamini)
LLM_API_KEY = os.getenv("LLM_API_KEY")

# LLM Provider configuration
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "anthropic")  # anthropic, openai, or groq
LLM_MODEL = os.getenv("LLM_MODEL")  # Optional: override default model

# Provider-specific API keys
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# CORS configuration
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:5173,http://localhost:3000").split(",")

# Application settings
DEBUG = os.getenv("DEBUG", "false").lower() == "true"
