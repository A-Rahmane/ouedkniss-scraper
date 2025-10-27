"""
Configuration settings for the Ouedkniss scraper.
"""
from typing import Dict, Any
from dataclasses import dataclass
import os
from dotenv import load_dotenv

load_dotenv()


@dataclass
class ScraperConfig:
    """Configuration for scraper behavior."""
    
    BASE_URL: str = "https://www.ouedkniss.com"
    USER_AGENT: str = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    REQUEST_TIMEOUT: int = 30
    RATE_LIMIT_DELAY: float = 1.0  # Seconds between requests
    MAX_RETRIES: int = 3
    CONCURRENT_REQUESTS: int = 5


@dataclass
class DatabaseConfig:
    """Configuration for MongoDB connection."""
    
    MONGODB_URI: str = os.getenv("MONGODB_URI", "mongodb://localhost:27017/")
    DATABASE_NAME: str = os.getenv("DATABASE_NAME", "ouedkniss_db")
    COLLECTION_NAME: str = "products"


@dataclass
class APIConfig:
    """Configuration for API server."""
    
    HOST: str = os.getenv("API_HOST", "0.0.0.0")
    PORT: int = int(os.getenv("API_PORT", "8000"))
    DEBUG: bool = os.getenv("DEBUG", "False").lower() == "true"


class Config:
    """Main configuration class."""
    
    scraper = ScraperConfig()
    database = DatabaseConfig()
    api = APIConfig()
