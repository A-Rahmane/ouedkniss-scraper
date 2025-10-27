"""
Product page scraper for Ouedkniss.
"""
import re
import logging
from typing import Optional, List, Dict, Any
from bs4 import BeautifulSoup
from datetime import datetime

from ..models.product import Product, SellerInfo, QuestionAnswer
from .base_scraper import BaseScraper


logger = logging.getLogger(__name__)


class ProductScraper(BaseScraper):
    """Scraper for Ouedkniss product pages."""
    
    def extract_product_id(self, url: str) -> Optional[str]:
        """Extract product ID from URL."""
        match = re.search(r'-d(\d+)$', url)
        return match.group(1) if match else None
    
    def extract_title(self, soup: BeautifulSoup) -> str:
        """Extract product title."""
        title_elem = soup.find('h1', class_=re.compile(r'title|heading'))
        if not title_elem:
            title_elem = soup.find('h1')
        
        return title_elem.get_text(strip=True) if title_elem else "Unknown Title"
    
    def extract_category_hierarchy(self, soup: BeautifulSoup, url: str) -> tuple:
        """
        Extract category and subcategories.
        
        Returns:
            Tuple of (main_category, subcategories_list)
        """
        # Try to find breadcrumbs
        breadcrumb = soup.find('nav', class_=re.compile(r'breadcrumb'))
        if not breadcrumb:
            breadcrumb = soup.find('ol', class_=re.compile(r'breadcrumb'))
        
        categories = []
        
        if breadcrumb:
            links = breadcrumb.find_all('a')
            for link in links[1:]:  # Skip home link
                category = link.get_text(strip=True)
                if category:
                    categories.append(category)
        
        # Fallback: extract from URL
        if not categories:
            path = url.split('/')[-1].split('-d')[0]
            categories = path.split('-')
        
        main_category = categories[0] if categories else "Unknown"
        subcategories = categories[1:] if len(categories) > 1 else []
        
        return main_category, subcategories
    
    def extract_price(self, soup: BeautifulSoup) -> tuple:
        """
        Extract price information.
        
        Returns:
            Tuple of (price, currency, is_negotiable)
        """
        price = None
        currency = "DZD"
        negotiable = False
        
        # Look for price element
        price_elem = soup.find(class_=re.compile(r'price', re.I))
        if not price_elem:
            price_elem = soup.find(string=re.compile(r'DA|دج|\d+'))
        
        if price_elem:
            price_text = price_elem.get_text() if hasattr(price_elem, 'get_text') else str(price_elem)
            
            # Extract numeric value
            price_match = re.search(r'([\d\s,.]+)', price_text)
            if price_match:
                price_str = price_match.group(1).replace(' ', '').replace(',', '')
                try:
                    price = float(price_str)
                except ValueError:
                    pass
            
            # Check for negotiable
            if re.search(r'negotiable|à débattre|négociable', price_text, re.I):
                negotiable = True
        
        return price, currency, negotiable
    
    def extract_description(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract product description."""
        desc_elem = soup.find(class_=re.compile(r'description|desc|content'))
        if not desc_elem:
            desc_elem = soup.find('div', id=re.compile(r'description'))
        
        if desc_elem:
            # Remove script and style elements
            for script in desc_elem(['script', 'style']):
                script.decompose()
            
            return desc_elem.get_text(separator='\n', strip=True)
        
        return None
    
    def extract_specifications(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Extract product specifications/details."""
        specs = {}
        
        # Look for specification table or list
        spec_containers = soup.find_all(class_=re.compile(r'spec|detail|info|caractéristiques'))
        
        for container in spec_containers:
            # Try to find key-value pairs
            rows = container.find_all(['tr', 'li', 'div'])
            
            for row in rows:
                # Look for label and value pattern
                label_elem = row.find(class_=re.compile(r'label|key|name'))
                value_elem = row.find(class_=re.compile(r'value|val|data'))
                
                if label_elem and value_elem:
                    key = label_elem.get_text(strip=True).rstrip(':')
                    value = value_elem.get_text(strip=True)
                    specs[key] = value
                else:
                    # Try to split text
                    text = row.get_text(strip=True)
                    if ':' in text:
                        parts = text.split(':', 1)
                        if len(parts) == 2:
                            specs[parts[0].strip()] = parts[1].strip()
        
        return specs
    
    def extract_images(self, soup: BeautifulSoup) -> List[str]:
        """Extract product image URLs."""
        images = []
        
        # Look for gallery or image container
        gallery = soup.find(class_=re.compile(r'gallery|slider|images|photos'))
        
        if gallery:
            img_tags = gallery.find_all('img')
        else:
            img_tags = soup.find_all('img')
        
        for img in img_tags:
            src = img.get('src') or img.get('data-src') or img.get('data-lazy')
            
            if src and not re.search(r'logo|icon|avatar|placeholder', src, re.I):
                # Convert to absolute URL if needed
                if src.startswith('//'):
                    src = 'https:' + src
                elif src.startswith('/'):
                    src = 'https://www.ouedkniss.com' + src
                
                if src not in images:
                    images.append(src)
        
        return images
    
    def extract_seller_info(self, soup: BeautifulSoup) -> Optional[SellerInfo]:
        """Extract seller information."""
        seller_container = soup.find(class_=re.compile(r'seller|vendor|author|contact'))
        
        if not seller_container:
            return None
        
        name = None
        phone = None
        email = None
        address = None
        location = {}
        
        # Extract name
        name_elem = seller_container.find(class_=re.compile(r'name|title'))
        if name_elem:
            name = name_elem.get_text(strip=True)
        
        # Extract phone
        phone_elem = seller_container.find(string=re.compile(r'\+?\d{10,}'))
        if phone_elem:
            phone_match = re.search(r'\+?\d{10,}', phone_elem)
            phone = phone_match.group(0) if phone_match else None
        
        # Extract email
        email_elem = seller_container.find(string=re.compile(r'[\w\.-]+@[\w\.-]+\.\w+'))
        if email_elem:
            email_match = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', email_elem)
            email = email_match.group(0) if email_match else None
        
        # Extract address/location
        location_elem = seller_container.find(class_=re.compile(r'location|address|ville|city'))
        if location_elem:
            address = location_elem.get_text(strip=True)
            
            # Try to parse structured location
            location_parts = address.split(',')
            if len(location_parts) >= 2:
                location = {
                    'city': location_parts[0].strip(),
                    'region': location_parts[1].strip()
                }
        
        if name:
            return SellerInfo(
                name=name,
                phone=phone,
                email=email,
                address=address,
                location=location if location else None
            )
        
        return None
    
    def extract_questions_answers(self, soup: BeautifulSoup) -> List[QuestionAnswer]:
        """Extract Q&A section."""
        qa_list = []
        
        qa_container = soup.find(class_=re.compile(r'question|q-a|qna|faq'))
        
        if not qa_container:
            return qa_list
        
        qa_items = qa_container.find_all(class_=re.compile(r'question|item|qa'))
        
        for item in qa_items:
            question_elem = item.find(class_=re.compile(r'question|q\b'))
            answer_elem = item.find(class_=re.compile(r'answer|a\b|response'))
            
            if question_elem:
                question = question_elem.get_text(strip=True)
                answer = answer_elem.get_text(strip=True) if answer_elem else None
                
                qa_list.append(QuestionAnswer(
                    question=question,
                    answer=answer
                ))
        
        return qa_list
    
    def extract_metadata(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Extract additional metadata."""
        metadata = {}
        
        # Views count
        views_elem = soup.find(string=re.compile(r'views?|vues?|\d+\s*vue'))
        if views_elem:
            views_match = re.search(r'(\d+)', views_elem)
            if views_match:
                metadata['views'] = int(views_match.group(1))
        
        # Last updated
        date_elem = soup.find(class_=re.compile(r'date|time|updated'))
        if date_elem:
            metadata['last_updated'] = date_elem.get_text(strip=True)
        
        return metadata
    
    async def scrape_product(self, url: str) -> Optional[Product]:
        """
        Scrape a product page and return Product object.
        
        Args:
            url: Product page URL
            
        Returns:
            Product object or None if scraping failed
        """
        try:
            html = await self.fetch_page(url)
            if not html:
                logger.error(f"Failed to fetch product page: {url}")
                return None
            
            soup = BeautifulSoup(html, 'html.parser')
            
            # Extract all data
            product_id = self.extract_product_id(url)
            title = self.extract_title(soup)
            category, subcategories = self.extract_category_hierarchy(soup, url)
            price, currency, negotiable = self.extract_price(soup)
            description = self.extract_description(soup)
            specifications = self.extract_specifications(soup)
            images = self.extract_images(soup)
            seller = self.extract_seller_info(soup)
            qa = self.extract_questions_answers(soup)
            metadata = self.extract_metadata(soup)
            
            # Create Product object
            product = Product(
                product_id=product_id,
                url=url,
                title=title,
                category=category,
                subcategories=subcategories,
                price=price,
                currency=currency,
                negotiable=negotiable,
                description=description,
                specifications=specifications,
                images=images,
                seller=seller,
                questions_answers=qa,
                views=metadata.get('views'),
                last_updated=metadata.get('last_updated'),
                scraped_at=datetime.utcnow()
            )
            
            logger.info(f"Successfully scraped product: {title}")
            return product
            
        except Exception as e:
            logger.error(f"Error scraping product {url}: {e}")
            return None