"""
Main script to run the Ouedkniss scraper.
"""
import asyncio
import argparse
import logging
from typing import List

from src.crawler.crawler import OuedknissCrawler
from src.crawler.url_filter import URLFilter
from src.scraper.product_scraper import ProductScraper
from src.database.mongodb_handler import MongoDBHandler
from src.config.settings import Config


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def crawl_and_scrape(
    category_url: str = None,
    max_pages: int = None,
    max_products: int = None
):
    """
    Main function to crawl and scrape Ouedkniss.
    
    Args:
        category_url: Specific category URL to scrape (None for all)
        max_pages: Maximum pages to crawl per category
        max_products: Maximum products to scrape
    """
    logger.info("Starting Ouedkniss scraper...")
    
    # Initialize components
    url_filter = URLFilter()
    
    async with OuedknissCrawler(url_filter=url_filter) as crawler:
        async with ProductScraper() as scraper:
            async with MongoDBHandler() as db:
                
                # Crawl for product URLs
                if category_url:
                    logger.info(f"Crawling category: {category_url}")
                    product_urls = await crawler.crawl_category(
                        category_url,
                        max_pages=max_pages
                    )
                else:
                    logger.info("Crawling all categories...")
                    product_urls = await crawler.crawl_all_categories()
                
                logger.info(f"Found {len(product_urls)} product URLs")
                
                # Limit if max_products specified
                if max_products:
                    product_urls = list(product_urls)[:max_products]
                    logger.info(f"Limited to {len(product_urls)} products")
                
                # Scrape products
                scraped_count = 0
                failed_count = 0
                
                for i, url in enumerate(product_urls, 1):
                    logger.info(f"Scraping product {i}/{len(product_urls)}: {url}")
                    
                    product = await scraper.scrape_product(url)
                    
                    if product:
                        success = await db.insert_product(product)
                        if success:
                            scraped_count += 1
                        else:
                            failed_count += 1
                    else:
                        failed_count += 1
                    
                    # Log progress every 10 products
                    if i % 10 == 0:
                        logger.info(
                            f"Progress: {i}/{len(product_urls)} - "
                            f"Scraped: {scraped_count}, Failed: {failed_count}"
                        )
                
                logger.info(
                    f"Scraping completed! "
                    f"Total: {len(product_urls)}, "
                    f"Success: {scraped_count}, "
                    f"Failed: {failed_count}"
                )
                
                # Get statistics
                stats = await db.get_statistics()
                logger.info(f"Database statistics: {stats}")


async def scrape_specific_urls(urls: List[str]):
    """
    Scrape specific product URLs.
    
    Args:
        urls: List of product URLs to scrape
    """
    logger.info(f"Scraping {len(urls)} specific URLs...")
    
    async with ProductScraper() as scraper:
        async with MongoDBHandler() as db:
            
            scraped_count = 0
            
            for url in urls:
                logger.info(f"Scraping: {url}")
                
                product = await scraper.scrape_product(url)
                
                if product:
                    await db.insert_product(product)
                    scraped_count += 1
            
            logger.info(f"Scraped {scraped_count}/{len(urls)} products")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Ouedkniss Web Scraper"
    )
    
    parser.add_argument(
        '--mode',
        choices=['crawl', 'scrape', 'api'],
        default='crawl',
        help='Operation mode'
    )
    
    parser.add_argument(
        '--category',
        type=str,
        help='Specific category URL to scrape'
    )
    
    parser.add_argument(
        '--max-pages',
        type=int,
        help='Maximum pages to crawl per category'
    )
    
    parser.add_argument(
        '--max-products',
        type=int,
        help='Maximum products to scrape'
    )
    
    parser.add_argument(
        '--urls',
        nargs='+',
        help='Specific product URLs to scrape'
    )
    
    args = parser.parse_args()
    
    if args.mode == 'api':
        # Run API server
        import uvicorn
        from src.api.app import app
        
        config = Config.api
        logger.info(f"Starting API server on {config.HOST}:{config.PORT}")
        
        uvicorn.run(
            app,
            host=config.HOST,
            port=config.PORT,
            log_level="info"
        )
    
    elif args.mode == 'scrape' and args.urls:
        # Scrape specific URLs
        asyncio.run(scrape_specific_urls(args.urls))
    
    else:
        # Crawl and scrape
        asyncio.run(crawl_and_scrape(
            category_url=args.category,
            max_pages=args.max_pages,
            max_products=args.max_products
        ))


if __name__ == "__main__":
    main()