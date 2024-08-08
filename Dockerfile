yamlCopy code
version: '3.8'

services:
  web:
    build: .
    ports:
      - "8000:8000"
    environment:
      - SUPABASE_URL=${SUPABASE_URL}
      - SUPABASE_API_KEY=${SUPABASE_API_KEY}
    #   - LLM_API_KEY=${LLM_API_KEY}

