from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # API Configuration
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    DEBUG: bool = True
    
    # Rate Limiting
    MAX_REQUESTS_PER_MINUTE: int = 60
    
    # YouTube API
    YOUTUBE_API_KEY: Optional[str] = None
    
    class Config:
        env_file = ".env"

settings = Settings()