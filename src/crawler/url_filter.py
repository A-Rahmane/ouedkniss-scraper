"""
URL filtering and classification for Ouedkniss crawler.
"""
import re
from typing import Optional, Tuple, List
from enum import Enum
from urllib.parse import urlparse, urljoin


class URLType(Enum):
    """Types of URLs in Ouedkniss."""
    
    HOME = "home"
    CATEGORY = "category"
    SUBCATEGORY = "subcategory"
    PRODUCT = "product"
    PAGINATION = "pagination"
    INVALID = "invalid"


class URLFilter:
    """Filter and classify Ouedkniss URLs."""
    
    def __init__(self, base_url: str = "https://www.ouedkniss.com"):
        self.base_url = base_url
        self.product_pattern = re.compile(
            r'/[a-z-]+-[a-z]+-[a-z-]+-d\d+$'
        )
        self.category_pattern = re.compile(
            r'^/([a-z-]+)/(\d+)$'
        )
    
    def is_valid_domain(self, url: str) -> bool:
        """Check if URL belongs to Ouedkniss domain."""
        parsed = urlparse(url)
        return parsed.netloc in ['www.ouedkniss.com', 'ouedkniss.com', '']
    
    def normalize_url(self, url: str) -> str:
        """Normalize URL to absolute format."""
        if url.startswith('/'):
            return urljoin(self.base_url, url)
        return url
    
    def classify_url(self, url: str) -> URLType:
        """Classify URL type."""
        if not self.is_valid_domain(url):
            return URLType.INVALID
        
        parsed = urlparse(url)
        path = parsed.path
        
        # Home page
        if path == '/' or path == '':
            return URLType.HOME
        
        # Product page (ends with -dXXXXXX)
        if re.search(r'-d\d+$', path):
            return URLType.PRODUCT
        
        # Category/Subcategory with pagination
        category_match = self.category_pattern.match(path)
        if category_match:
            category_path = category_match.group(1)
            page_num = category_match.group(2)
            
            # Count dashes to determine depth
            depth = category_path.count('-')
            
            if depth == 0:
                return URLType.CATEGORY
            else:
                return URLType.SUBCATEGORY
        
        return URLType.INVALID
    
    def extract_category_info(self, url: str) -> Optional[Tuple[List[str], int]]:
        """
        Extract category hierarchy and page number from URL.
        
        Returns:
            Tuple of (category_list, page_number) or None
        """
        parsed = urlparse(url)
        path = parsed.path
        
        match = self.category_pattern.match(path)
        if not match:
            return None
        
        category_path = match.group(1)
        page_num = int(match.group(2))
        
        categories = category_path.split('-')
        
        return (categories, page_num)
    
    def extract_product_id(self, url: str) -> Optional[str]:
        """Extract product ID from product URL."""
        match = re.search(r'-d(\d+)$', urlparse(url).path)
        if match:
            return match.group(1)
        return None
    
    def should_crawl(self, url: str) -> bool:
        """Determine if URL should be crawled."""
        url_type = self.classify_url(url)
        return url_type in [
            URLType.HOME,
            URLType.CATEGORY,
            URLType.SUBCATEGORY,
            URLType.PRODUCT
        ]