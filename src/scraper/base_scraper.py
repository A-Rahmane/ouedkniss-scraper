"""
Base scraper class with common functionality.
"""
import asyncio
import logging
from typing import Optional
import aiohttp

from ..config.settings import Config


logger = logging.getLogger(__name__)


class BaseScraper:
    """Base scraper with HTTP functionality."""
    
    def __init__(self):
        self.config = Config.scraper
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def __aenter__(self):
        """Async context manager entry."""
        self.session = aiohttp.ClientSession(
            headers={'User-Agent': self.config.USER_AGENT},
            timeout=aiohttp.ClientTimeout(total=self.config.REQUEST_TIMEOUT)
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.close()
    
    async def fetch_page(self, url: str) -> Optional[str]:
        """Fetch a page with retries."""
        for attempt in range(self.config.MAX_RETRIES):
            try:
                await asyncio.sleep(self.config.RATE_LIMIT_DELAY)
                
                async with self.session.get(url) as response:
                    if response.status == 200:
                        return await response.text()
                    else:
                        logger.warning(f"Status {response.status} for {url}")
            
            except Exception as e:
                logger.error(f"Error fetching {url}: {e}, attempt {attempt + 1}")
                
                if attempt < self.config.MAX_RETRIES - 1:
                    await asyncio.sleep(2 ** attempt)
        
        return None