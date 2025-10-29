import os
from pydantic_settings import BaseSettings

# Centralized configuration class for managing environment variables
class Settings(BaseSettings):
    # Required API key for OpenAI access
    openai_api_key: str

    # Default environment label (useful for switching between dev/prod)
    environment: str = "development"

    # Controls verbosity for logging
    log_level: str = "INFO"

    # Parameters for text chunking when processing documents
    chunk_size: int = 2500
    overlap: int = 400

    class Config:
        # Automatically load variables from .env if present
        env_file = ".env"
        # Ignore any unexpected environment variables
        extra = "ignore"

# Retrieve API key directly from environment (used for quick access)
settings = os.getenv("OPENAI_API_KEY")
