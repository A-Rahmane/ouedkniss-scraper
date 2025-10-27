"""
Web crawler for Ouedkniss website.
"""
import asyncio
import logging
from typing import Set, List, Optional
from urllib.parse import urljoin
import aiohttp
from bs4 import BeautifulSoup
from asyncio import Semaphore

from ..config.settings import Config
from .url_filter import URLFilter, URLType


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class OuedknissCrawler:
    """Asynchronous crawler for Ouedkniss."""
    
    def __init__(
        self,
        url_filter: Optional[URLFilter] = None,
        max_concurrent: int = None
    ):
        self.config = Config.scraper
        self.url_filter = url_filter or URLFilter()
        self.visited_urls: Set[str] = set()
        self.product_urls: Set[str] = set()
        self.max_concurrent = max_concurrent or self.config.CONCURRENT_REQUESTS
        self.semaphore = Semaphore(self.max_concurrent)
        
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
        """
        Fetch a page with rate limiting and retries.
        
        Args:
            url: URL to fetch
            
        Returns:
            Page HTML content or None
        """
        async with self.semaphore:
            for attempt in range(self.config.MAX_RETRIES):
                try:
                    await asyncio.sleep(self.config.RATE_LIMIT_DELAY)
                    
                    async with self.session.get(url) as response:
                        if response.status == 200:
                            return await response.text()
                        elif response.status == 404:
                            logger.warning(f"Page not found: {url}")
                            return None
                        else:
                            logger.warning(
                                f"Status {response.status} for {url}, "
                                f"attempt {attempt + 1}/{self.config.MAX_RETRIES}"
                            )
                
                except asyncio.TimeoutError:
                    logger.warning(f"Timeout for {url}, attempt {attempt + 1}")
                except Exception as e:
                    logger.error(f"Error fetching {url}: {e}, attempt {attempt + 1}")
                
                if attempt < self.config.MAX_RETRIES - 1:
                    await asyncio.sleep(2 ** attempt)  # Exponential backoff
            
            return None
    
    def extract_links(self, html: str, base_url: str) -> List[str]:
        """
        Extract all links from HTML content.
        
        Args:
            html: HTML content
            base_url: Base URL for resolving relative links
            
        Returns:
            List of absolute URLs
        """
        soup = BeautifulSoup(html, 'html.parser')
        links = []
        
        for link in soup.find_all('a', href=True):
            href = link['href']
            absolute_url = urljoin(base_url, href)
            normalized_url = self.url_filter.normalize_url(absolute_url)
            
            if self.url_filter.should_crawl(normalized_url):
                links.append(normalized_url)
        
        return links
    
    async def crawl_page(self, url: str) -> List[str]:
        """
        Crawl a single page and return discovered URLs.
        
        Args:
            url: URL to crawl
            
        Returns:
            List of discovered URLs
        """
        if url in self.visited_urls:
            return []
        
        self.visited_urls.add(url)
        logger.info(f"Crawling: {url}")
        
        html = await self.fetch_page(url)
        if not html:
            return []
        
        # Classify URL
        url_type = self.url_filter.classify_url(url)
        
        # If it's a product page, add to product URLs
        if url_type == URLType.PRODUCT:
            self.product_urls.add(url)
            logger.info(f"Found product: {url}")
            return []
        
        # Extract and return links
        links = self.extract_links(html, url)
        return [link for link in links if link not in self.visited_urls]
    
    async def crawl_category(
        self,
        category_url: str,
        max_pages: Optional[int] = None
    ) -> Set[str]:
        """
        Crawl a category and all its pages.
        
        Args:
            category_url: Starting category URL
            max_pages: Maximum number of pages to crawl (None for all)
            
        Returns:
            Set of product URLs found
        """
        category_info = self.url_filter.extract_category_info(category_url)
        if not category_info:
            logger.error(f"Invalid category URL: {category_url}")
            return set()
        
        categories, _ = category_info
        base_category = '/'.join(categories)
        
        page = 1
        urls_to_visit = [f"{self.config.BASE_URL}/{base_category}/{page}"]
        
        while urls_to_visit and (max_pages is None or page <= max_pages):
            current_url = urls_to_visit.pop(0)
            new_urls = await self.crawl_page(current_url)
            
            # Add new URLs that haven't been visited
            for new_url in new_urls:
                if new_url not in self.visited_urls:
                    urls_to_visit.append(new_url)
            
            # Check for next page
            page += 1
            next_page_url = f"{self.config.BASE_URL}/{base_category}/{page}"
            
            if next_page_url not in self.visited_urls and page > 1:
                # Check if we found products on this page, if yes continue
                if len(self.product_urls) > 0:
                    urls_to_visit.append(next_page_url)
        
        return self.product_urls
    
    async def crawl_all_categories(self) -> Set[str]:
        """
        Crawl all categories starting from home page.
        
        Returns:
            Set of all product URLs found
        """
        home_url = self.config.BASE_URL
        
        # First, get all category links from home page
        logger.info("Fetching categories from home page...")
        html = await self.fetch_page(home_url)
        
        if not html:
            logger.error("Failed to fetch home page")
            return set()
        
        ## # SECTION TO BE REMOVED # ##
        print(html)
        #### ## END OF SECTION ## ####
        
        category_links = self.extract_links(html, home_url)
        category_urls = [
            link for link in category_links
            if self.url_filter.classify_url(link) in [URLType.CATEGORY, URLType.SUBCATEGORY]
        ]
        
        logger.info(f"Found {len(category_urls)} category URLs")
        
        # Crawl each category
        tasks = [self.crawl_category(cat_url) for cat_url in category_urls[:3]]  # Limit for testing
        await asyncio.gather(*tasks)
        
        return self.product_urls