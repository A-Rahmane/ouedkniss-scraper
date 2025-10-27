"""
MongoDB database handler for storing scraped products.
"""
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.errors import DuplicateKeyError, PyMongoError

from ..config.settings import Config
from ..models.product import Product


logger = logging.getLogger(__name__)


class MongoDBHandler:
    """Handler for MongoDB operations."""
    
    def __init__(self):
        self.config = Config.database
        self.client: Optional[AsyncIOMotorClient] = None
        self.db = None
        self.collection = None
    
    async def connect(self):
        """Establish connection to MongoDB."""
        try:
            self.client = AsyncIOMotorClient(self.config.MONGODB_URI)
            self.db = self.client[self.config.DATABASE_NAME]
            self.collection = self.db[self.config.COLLECTION_NAME]
            
            # Create indexes
            await self.create_indexes()
            
            logger.info(f"Connected to MongoDB: {self.config.DATABASE_NAME}")
            
        except Exception as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            raise
    
    async def disconnect(self):
        """Close MongoDB connection."""
        if self.client:
            self.client.close()
            logger.info("Disconnected from MongoDB")
    
    async def create_indexes(self):
        """Create database indexes for efficient querying."""
        try:
            # Unique index on product_id
            await self.collection.create_index("product_id", unique=True)
            
            # Index on category for filtering
            await self.collection.create_index("category")
            
            # Compound index on category and subcategories
            await self.collection.create_index([
                ("category", 1),
                ("subcategories", 1)
            ])
            
            # Index on price for range queries
            await self.collection.create_index("price")
            
            # Index on scraped_at for time-based queries
            await self.collection.create_index("scraped_at")
            
            # Text index on title and description for search
            await self.collection.create_index([
                ("title", "text"),
                ("description", "text")
            ])
            
            logger.info("Created database indexes")
            
        except Exception as e:
            logger.error(f"Error creating indexes: {e}")
    
    async def insert_product(self, product: Product) -> bool:
        """
        Insert a product into the database.
        
        Args:
            product: Product object to insert
            
        Returns:
            True if successful, False otherwise
        """
        try:
            product_dict = product.to_dict()
            await self.collection.insert_one(product_dict)
            logger.info(f"Inserted product: {product.product_id}")
            return True
            
        except DuplicateKeyError:
            logger.warning(f"Product already exists: {product.product_id}")
            # Update instead
            return await self.update_product(product)
            
        except Exception as e:
            logger.error(f"Error inserting product {product.product_id}: {e}")
            return False
    
    async def insert_many_products(self, products: List[Product]) -> int:
        """
        Insert multiple products into the database.
        
        Args:
            products: List of Product objects
            
        Returns:
            Number of products successfully inserted
        """
        if not products:
            return 0
        
        product_dicts = [p.to_dict() for p in products]
        inserted_count = 0
        
        try:
            result = await self.collection.insert_many(
                product_dicts,
                ordered=False  # Continue on duplicates
            )
            inserted_count = len(result.inserted_ids)
            logger.info(f"Inserted {inserted_count} products")
            
        except Exception as e:
            logger.error(f"Error in bulk insert: {e}")
            # Fall back to individual inserts
            for product in products:
                if await self.insert_product(product):
                    inserted_count += 1
        
        return inserted_count
    
    async def update_product(self, product: Product) -> bool:
        """
        Update an existing product.
        
        Args:
            product: Product object with updated data
            
        Returns:
            True if successful, False otherwise
        """
        try:
            product_dict = product.to_dict()
            product_dict['updated_at'] = datetime.utcnow()
            
            result = await self.collection.update_one(
                {"product_id": product.product_id},
                {"$set": product_dict}
            )
            
            if result.modified_count > 0:
                logger.info(f"Updated product: {product.product_id}")
                return True
            else:
                logger.warning(f"No changes for product: {product.product_id}")
                return False
                
        except Exception as e:
            logger.error(f"Error updating product {product.product_id}: {e}")
            return False
    
    async def get_product_by_id(self, product_id: str) -> Optional[Product]:
        """
        Retrieve a product by its ID.
        
        Args:
            product_id: Product ID
            
        Returns:
            Product object or None
        """
        try:
            doc = await self.collection.find_one({"product_id": product_id})
            
            if doc:
                doc.pop('_id', None)  # Remove MongoDB ID
                return Product.from_dict(doc)
            
            return None
            
        except Exception as e:
            logger.error(f"Error retrieving product {product_id}: {e}")
            return None
    
    async def get_products(
        self,
        filter_dict: Optional[Dict[str, Any]] = None,
        skip: int = 0,
        limit: int = 100,
        sort_by: Optional[str] = None,
        sort_order: int = -1
    ) -> List[Product]:
        """
        Retrieve products with filtering and pagination.
        
        Args:
            filter_dict: MongoDB filter dictionary
            skip: Number of documents to skip
            limit: Maximum number of documents to return
            sort_by: Field to sort by
            sort_order: Sort order (1 for ascending, -1 for descending)
            
        Returns:
            List of Product objects
        """
        try:
            filter_dict = filter_dict or {}
            
            cursor = self.collection.find(filter_dict).skip(skip).limit(limit)
            
            if sort_by:
                cursor = cursor.sort(sort_by, sort_order)
            
            products = []
            async for doc in cursor:
                doc.pop('_id', None)
                products.append(Product.from_dict(doc))
            
            return products
            
        except Exception as e:
            logger.error(f"Error retrieving products: {e}")
            return []
    
    async def count_products(self, filter_dict: Optional[Dict[str, Any]] = None) -> int:
        """
        Count products matching filter.
        
        Args:
            filter_dict: MongoDB filter dictionary
            
        Returns:
            Count of matching products
        """
        try:
            filter_dict = filter_dict or {}
            count = await self.collection.count_documents(filter_dict)
            return count
            
        except Exception as e:
            logger.error(f"Error counting products: {e}")
            return 0
    
    async def search_products(
        self,
        search_text: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[Product]:
        """
        Full-text search on products.
        
        Args:
            search_text: Text to search for
            skip: Number of documents to skip
            limit: Maximum number of documents to return
            
        Returns:
            List of matching Product objects
        """
        try:
            cursor = self.collection.find(
                {"$text": {"$search": search_text}}
            ).skip(skip).limit(limit)
            
            products = []
            async for doc in cursor:
                doc.pop('_id', None)
                products.append(Product.from_dict(doc))
            
            return products
            
        except Exception as e:
            logger.error(f"Error searching products: {e}")
            return []
    
    async def get_categories(self) -> List[str]:
        """
        Get list of all unique categories.
        
        Returns:
            List of category names
        """
        try:
            categories = await self.collection.distinct("category")
            return sorted(categories)
            
        except Exception as e:
            logger.error(f"Error retrieving categories: {e}")
            return []
    
    async def get_statistics(self) -> Dict[str, Any]:
        """
        Get database statistics.
        
        Returns:
            Dictionary with statistics
        """
        try:
            total_products = await self.collection.count_documents({})
            
            # Products by category
            pipeline = [
                {"$group": {
                    "_id": "$category",
                    "count": {"$sum": 1}
                }},
                {"$sort": {"count": -1}}
            ]
            category_stats = []
            async for doc in self.collection.aggregate(pipeline):
                category_stats.append({
                    "category": doc["_id"],
                    "count": doc["count"]
                })
            
            # Price statistics
            price_pipeline = [
                {"$match": {"price": {"$ne": None}}},
                {"$group": {
                    "_id": None,
                    "avg_price": {"$avg": "$price"},
                    "min_price": {"$min": "$price"},
                    "max_price": {"$max": "$price"}
                }}
            ]
            price_stats = None
            async for doc in self.collection.aggregate(price_pipeline):
                price_stats = {
                    "average": doc.get("avg_price"),
                    "minimum": doc.get("min_price"),
                    "maximum": doc.get("max_price")
                }
            
            return {
                "total_products": total_products,
                "categories": category_stats,
                "price_statistics": price_stats
            }
            
        except Exception as e:
            logger.error(f"Error retrieving statistics: {e}")
            return {}
    
    async def delete_product(self, product_id: str) -> bool:
        """
        Delete a product by ID.
        
        Args:
            product_id: Product ID to delete
            
        Returns:
            True if successful, False otherwise
        """
        try:
            result = await self.collection.delete_one({"product_id": product_id})
            
            if result.deleted_count > 0:
                logger.info(f"Deleted product: {product_id}")
                return True
            else:
                logger.warning(f"Product not found: {product_id}")
                return False
                
        except Exception as e:
            logger.error(f"Error deleting product {product_id}: {e}")
            return False
    
    async def __aenter__(self):
        """Async context manager entry."""
        await self.connect()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.disconnect()
