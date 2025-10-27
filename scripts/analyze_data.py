"""
Utility script for analyzing scraped data.
"""
import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.database.mongodb_handler import MongoDBHandler


async def analyze_data():
    """Analyze scraped data and print statistics."""
    
    async with MongoDBHandler() as db:
        print("=" * 60)
        print("OUEDKNISS DATA ANALYSIS")
        print("=" * 60)
        
        # Get statistics
        stats = await db.get_statistics()
        
        print(f"\n📊 Total Products: {stats.get('total_products', 0)}")
        
        # Category breakdown
        print("\n📁 Products by Category:")
        print("-" * 60)
        categories = stats.get('categories', [])
        for cat in categories[:10]:  # Top 10 categories
            print(f"  {cat['category']:30} {cat['count']:>10} products")
        
        if len(categories) > 10:
            print(f"  ... and {len(categories) - 10} more categories")
        
        # Price statistics
        price_stats = stats.get('price_statistics')
        if price_stats:
            print("\n💰 Price Statistics:")
            print("-" * 60)
            print(f"  Average Price: {price_stats.get('average', 0):>15,.2f} DZD")
            print(f"  Minimum Price: {price_stats.get('minimum', 0):>15,.2f} DZD")
            print(f"  Maximum Price: {price_stats.get('maximum', 0):>15,.2f} DZD")
        
        # Sample products
        print("\n📦 Sample Products:")
        print("-" * 60)
        products = await db.get_products(limit=5, sort_by="scraped_at", sort_order=-1)
        
        for i, product in enumerate(products, 1):
            print(f"\n  {i}. {product.title}")
            print(f"     Category: {product.category}")
            print(f"     Price: {product.price:,.0f} {product.currency}" if product.price else "     Price: N/A")
            print(f"     Images: {len(product.images)}")
            print(f"     URL: {product.url}")
        
        print("\n" + "=" * 60)


if __name__ == "__main__":
    asyncio.run(analyze_data())