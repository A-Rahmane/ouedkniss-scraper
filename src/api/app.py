"""
FastAPI application for serving scraped data.
"""
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
import logging

from ..config.settings import Config
from ..database.mongodb_handler import MongoDBHandler
from ..models.product import Product


logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Ouedkniss Scraper API",
    description="API for accessing scraped Ouedkniss product data",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database handler
db_handler = MongoDBHandler()


# Pydantic models for API
class ProductResponse(BaseModel):
    """Response model for product data."""
    product_id: str
    url: str
    title: str
    category: str
    subcategories: List[str]
    price: Optional[float]
    currency: str
    description: Optional[str]
    images: List[str]
    
    class Config:
        from_attributes = True


class ProductListResponse(BaseModel):
    """Response model for product list."""
    total: int
    page: int
    page_size: int
    products: List[ProductResponse]


class StatisticsResponse(BaseModel):
    """Response model for statistics."""
    total_products: int
    categories: List[Dict[str, Any]]
    price_statistics: Optional[Dict[str, float]]


# Startup and shutdown events
@app.on_event("startup")
async def startup_event():
    """Initialize database connection on startup."""
    await db_handler.connect()
    logger.info("API server started")


@app.on_event("shutdown")
async def shutdown_event():
    """Close database connection on shutdown."""
    await db_handler.disconnect()
    logger.info("API server stopped")


# API Endpoints
@app.get("/", tags=["General"])
async def root():
    """Root endpoint."""
    return {
        "message": "Ouedkniss Scraper API",
        "version": "1.0.0",
        "endpoints": {
            "products": "/products",
            "product_by_id": "/products/{product_id}",
            "search": "/search",
            "categories": "/categories",
            "statistics": "/statistics"
        }
    }


@app.get("/health", tags=["General"])
async def health_check():
    """Health check endpoint."""
    try:
        count = await db_handler.count_products()
        return {
            "status": "healthy",
            "database": "connected",
            "total_products": count
        }
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Service unavailable: {str(e)}")


@app.get("/products", response_model=ProductListResponse, tags=["Products"])
async def get_products(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    category: Optional[str] = Query(None, description="Filter by category"),
    min_price: Optional[float] = Query(None, description="Minimum price"),
    max_price: Optional[float] = Query(None, description="Maximum price"),
    sort_by: Optional[str] = Query("scraped_at", description="Sort field"),
    sort_order: int = Query(-1, description="Sort order (1: asc, -1: desc)")
):
    """
    Get products with filtering and pagination.
    """
    try:
        # Build filter
        filter_dict = {}
        
        if category:
            filter_dict["category"] = category
        
        if min_price is not None or max_price is not None:
            price_filter = {}
            if min_price is not None:
                price_filter["$gte"] = min_price
            if max_price is not None:
                price_filter["$lte"] = max_price
            filter_dict["price"] = price_filter
        
        # Calculate skip
        skip = (page - 1) * page_size
        
        # Get products
        products = await db_handler.get_products(
            filter_dict=filter_dict,
            skip=skip,
            limit=page_size,
            sort_by=sort_by,
            sort_order=sort_order
        )
        
        # Get total count
        total = await db_handler.count_products(filter_dict)
        
        return ProductListResponse(
            total=total,
            page=page,
            page_size=page_size,
            products=[ProductResponse(**p.to_dict()) for p in products]
        )
        
    except Exception as e:
        logger.error(f"Error getting products: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/products/{product_id}", response_model=Dict[str, Any], tags=["Products"])
async def get_product_by_id(product_id: str):
    """
    Get a specific product by ID.
    """
    try:
        product = await db_handler.get_product_by_id(product_id)
        
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")
        
        return product.to_dict()
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting product {product_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/search", response_model=ProductListResponse, tags=["Products"])
async def search_products(
    q: str = Query(..., description="Search query"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page")
):
    """
    Full-text search for products.
    """
    try:
        skip = (page - 1) * page_size
        
        products = await db_handler.search_products(
            search_text=q,
            skip=skip,
            limit=page_size
        )
        
        # Note: Getting exact count for text search is expensive
        # For now, just return the number of results
        total = len(products)
        
        return ProductListResponse(
            total=total,
            page=page,
            page_size=page_size,
            products=[ProductResponse(**p.to_dict()) for p in products]
        )
        
    except Exception as e:
        logger.error(f"Error searching products: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/categories", response_model=List[str], tags=["Categories"])
async def get_categories():
    """
    Get list of all categories.
    """
    try:
        categories = await db_handler.get_categories()
        return categories
        
    except Exception as e:
        logger.error(f"Error getting categories: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/statistics", response_model=StatisticsResponse, tags=["Statistics"])
async def get_statistics():
    """
    Get database statistics.
    """
    try:
        stats = await db_handler.get_statistics()
        return StatisticsResponse(**stats)
        
    except Exception as e:
        logger.error(f"Error getting statistics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/products/{product_id}", tags=["Products"])
async def delete_product(product_id: str):
    """
    Delete a product by ID.
    """
    try:
        success = await db_handler.delete_product(product_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="Product not found")
        
        return {"message": f"Product {product_id} deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting product {product_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Run API server
if __name__ == "__main__":
    import uvicorn
    config = Config.api
    uvicorn.run(
        "src.api.app:app",
        host=config.HOST,
        port=config.PORT,
        reload=config.DEBUG
    )