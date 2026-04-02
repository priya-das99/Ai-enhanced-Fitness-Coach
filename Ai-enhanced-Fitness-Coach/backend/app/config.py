# app/config.py
# Application configuration

from pydantic_settings import BaseSettings
from typing import List
import os

class Settings(BaseSettings):
    # Project
    PROJECT_NAME: str = "Chat Assistant API"
    VERSION: str = "1.0.0"
    API_V1_PREFIX: str = "/api/v1"
    
    # Security
    SECRET_KEY: str = "your-secret-key-change-this-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    
    # Database - Support both SQLite (local) and PostgreSQL (deployment)
    DATABASE_URL: str = ""
    DATABASE_PATH: str = os.path.join(os.path.dirname(__file__), '..', 'mood_capture.db')
    
    @property
    def is_postgresql(self) -> bool:
        """Check if using PostgreSQL database"""
        return self.DATABASE_URL.startswith('postgresql://') or self.DATABASE_URL.startswith('postgres://')
    
    @property
    def database_config(self) -> dict:
        """Get database configuration based on environment"""
        if self.is_postgresql:
            return {
                'type': 'postgresql',
                'url': self.DATABASE_URL
            }
        else:
            return {
                'type': 'sqlite',
                'path': self.DATABASE_PATH
            }
    
    # CORS - Allow local, CodeSandbox, and ngrok domains
    ALLOWED_ORIGINS: str = "http://localhost:8080,http://127.0.0.1:8080,http://localhost:8000,http://127.0.0.1:8000,https://*.codesandbox.io,https://*.csb.app,https://*.ngrok.io,https://*.ngrok-free.app"
    
    # OpenAI/LLM Configuration (Optional)
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4o-mini"
    OPENAI_TEMPERATURE: str = "0.1"
    
    @property
    def cors_origins(self) -> List[str]:
        """Parse CORS origins from comma-separated string"""
        return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",")]
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "allow"  # Allow extra fields from .env

settings = Settings()
