# Ouedkniss Web Scraper

A comprehensive, production-ready web scraper for Ouedkniss.com built with Python, featuring asynchronous crawling, MongoDB storage, and a REST API.

## Features

- ✅ **Asynchronous Crawling**: Efficient concurrent URL discovery
- ✅ **Smart URL Filtering**: Intelligent classification and filtering of URLs
- ✅ **Comprehensive Data Extraction**: Products, specs, images, seller info, Q&A
- ✅ **MongoDB Storage**: NoSQL database with proper indexing
- ✅ **REST API**: FastAPI-based API for data access
- ✅ **SOLID Principles**: Clean, maintainable, and extensible code
- ✅ **Rate Limiting**: Respectful scraping with configurable delays
- ✅ **Error Handling**: Robust retry mechanisms and logging

## Project Structure
```
ouedkniss_scraper/
├── src/
│   ├── config/          # Configuration settings
│   ├── models/          # Data models
│   ├── crawler/         # URL crawling logic
│   ├── scraper/         # Data extraction logic
│   ├── database/        # MongoDB operations
│   └── api/             # FastAPI application
├── tests/               # Unit tests
├── main.py             # Main entry point
├── requirements.txt    # Dependencies
└── README.md          # This file
```

## Installation

### Prerequisites

- Python 3.8+
- MongoDB 4.0+

### Setup

1. **Clone the repository**
```bash
   git clone https://github.com/A-Rahmane/ouedkniss_py_scraper.get
   cd ouedkniss_scraper
```

2. **Create virtual environment**
```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**
```bash
   pip install -r requirements.txt
```

4. **Configure environment**
```bash
   cp .env.example .env
   # Edit .env with your MongoDB URI and other settings
```

5. **Start MongoDB**
```bash
   # Make sure MongoDB is running
   mongod --dbpath /path/to/data
```

## Usage

### 1. Crawl and Scrape All Categories
```bash
python main.py --mode crawl
```

### 2. Scrape Specific Category
```bash
python main.py --mode crawl --category "https://www.ouedkniss.com/informatique/1"
```

### 3. Limit Crawling
```bash
# Limit to 5 pages per category
python main.py --mode crawl --max-pages 5

# Limit to 100 products total
python main.py --mode crawl --max-products 100
```

### 4. Scrape Specific URLs
```bash
python main.py --mode scrape --urls \
  "https://www.ouedkniss.com/macbooks-macbook-pro-2015-15-i7-16g-2tb-sdd-beni-messous-alger-algerie-d51606425" \
  "https://www.ouedkniss.com/..."
```

### 5. Start API Server
```bash
python main.py --mode api
```

The API will be available at `http://localhost:8000`

## API Documentation

Once the API server is running, visit:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### API Endpoints

#### General
- `GET /` - API information
- `GET /health` - Health check

#### Products
- `GET /products` - Get products with filtering and pagination
  - Query params: `page`, `page_size`, `category`, `min_price`, `max_price`, `sort_by`, `sort_order`
- `GET /products/{product_id}` - Get specific product
- `DELETE /products/{product_id}` - Delete product

#### Search
- `GET /search?q={query}` - Full-text search

#### Categories
- `GET /categories` - Get all categories

#### Statistics
- `GET /statistics` - Get database statistics

### API Examples

**Get products with filtering:**
```bash
curl "http://localhost:8000/products?category=informatique&min_price=10000&max_price=50000&page=1&page_size=20"
```

**Search products:**
```bash
curl "http://localhost:8000/search?q=macbook+pro"
```

**Get specific product:**
```bash
curl "http://localhost:8000/products/51606425"
```

**Get statistics:**
```bash
curl "http://localhost:8000/statistics"
```

## Configuration

Edit `.env` file or `src/config/settings.py` to configure:

### Scraper Settings
- `BASE_URL`: Base URL for Ouedkniss (default: https://www.ouedkniss.com)
- `USER_AGENT`: User agent string
- `REQUEST_TIMEOUT`: Request timeout in seconds (default: 30)
- `RATE_LIMIT_DELAY`: Delay between requests in seconds (default: 1.0)
- `MAX_RETRIES`: Maximum retry attempts (default: 3)
- `CONCURRENT_REQUESTS`: Number of concurrent requests (default: 5)

### Database Settings
- `MONGODB_URI`: MongoDB connection string
- `DATABASE_NAME`: Database name
- `COLLECTION_NAME`: Collection name for products

### API Settings
- `API_HOST`: API server host (default: 0.0.0.0)
- `API_PORT`: API server port (default: 8000)
- `DEBUG`: Debug mode (default: False)

## Architecture

### SOLID Principles Implementation

1. **Single Responsibility Principle (SRP)**
   - Each class has one clear responsibility
   - `URLFilter`: URL classification
   - `OuedknissCrawler`: URL discovery
   - `ProductScraper`: Data extraction
   - `MongoDBHandler`: Database operations

2. **Open/Closed Principle (OCP)**
   - `BaseScraper` provides extensible base functionality
   - New scrapers can extend `BaseScraper` without modification

3. **Liskov Substitution Principle (LSP)**
   - `ProductScraper` extends `BaseScraper` properly
   - Subclasses maintain parent contracts

4. **Interface Segregation Principle (ISP)**
   - Focused interfaces for specific operations
   - API endpoints are segregated by functionality

5. **Dependency Inversion Principle (DIP)**
   - High-level modules depend on abstractions
   - Configuration is injected, not hardcoded

### Design Patterns Used

- **Factory Pattern**: Model creation from dictionaries
- **Strategy Pattern**: Different URL classification strategies
- **Repository Pattern**: Database abstraction layer
- **Singleton Pattern**: Configuration management
- **Context Manager Pattern**: Resource management (async context managers)

## Data Model

### Product Structure
```python
{
    "product_id": "51606425",
    "url": "https://...",
    "title": "MacBook Pro 2015 15\" i7 16GB 2TB SSD",
    "category": "informatique",
    "subcategories": ["ordinateur-portable", "macbooks"],
    "price": 85000.0,
    "currency": "DZD",
    "negotiable": false,
    "description": "...",
    "specifications": {
        "Processor": "Intel Core i7",
        "RAM": "16GB",
        "Storage": "2TB SSD"
    },
    "images": ["https://...", "https://..."],
    "seller": {
        "name": "John Doe",
        "phone": "+213...",
        "address": "Beni Messous, Alger"
    },
    "questions_answers": [
        {
            "question": "Is it available?",
            "answer": "Yes"
        }
    ],
    "views": 1234,
    "scraped_at": "2024-01-15T10:30:00",
    "last_updated": "2024-01-14"
}
```

## Database Indexes

The scraper automatically creates the following indexes:

- Unique index on `product_id`
- Index on `category`
- Compound index on `(category, subcategories)`
- Index on `price` for range queries
- Index on `scraped_at` for time-based queries
- Text index on `(title, description)` for full-text search

## Error Handling

The scraper includes comprehensive error handling:

- **Network Errors**: Automatic retry with exponential backoff
- **Parsing Errors**: Graceful degradation, logs warnings
- **Database Errors**: Proper error messages and rollback
- **Rate Limiting**: Automatic delay between requests

## Logging

Logging is configured with different levels:
```python
import logging

# Set logging level
logging.basicConfig(level=logging.INFO)

# Logs include:
# - INFO: Progress updates, successful operations
# - WARNING: Retries, missing data
# - ERROR: Failed operations, exceptions
```

## Testing

Run tests with pytest:
```bash
# Install test dependencies
pip install pytest pytest-asyncio

# Run tests
pytest tests/

# Run with coverage
pytest --cov=src tests/
```

## Performance Considerations

### Optimization Tips

1. **Adjust Concurrency**: Increase `CONCURRENT_REQUESTS` for faster crawling
2. **Rate Limiting**: Adjust `RATE_LIMIT_DELAY` based on server response
3. **Database Indexing**: Indexes are created automatically
4. **Connection Pooling**: Motor handles connection pooling automatically

### Resource Usage

- **Memory**: ~100-500MB depending on concurrent requests
- **CPU**: Low to moderate
- **Network**: Dependent on `CONCURRENT_REQUESTS` and `RATE_LIMIT_DELAY`
- **Storage**: ~1-5KB per product in MongoDB

## Best Practices

### Ethical Scraping

1. ✅ Respects `robots.txt` (Ouedkniss allows all)
2. ✅ Rate limiting to avoid server overload
3. ✅ User-agent identification
4. ✅ Research and analytics purposes only

### Code Quality

- Type hints throughout
- Comprehensive docstrings
- Async/await for efficient I/O
- Error handling and logging
- Modular and testable design

## Troubleshooting

### Common Issues

**MongoDB Connection Failed**
```bash
# Check if MongoDB is running
sudo systemctl status mongodb

# Start MongoDB
sudo systemctl start mongodb
```

**Import Errors**
```bash
# Ensure you're in the virtual environment
source venv/bin/activate

# Reinstall dependencies
pip install -r requirements.txt
```

**Scraping Fails**
```bash
# Check network connectivity
# Verify URL format
# Check logs for specific errors
```

**API Not Starting**
```bash
# Check if port is available
lsof -i :8000

# Try different port
python main.py --mode api  # Edit config for different port
```

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is for educational and research purposes only. Please respect Ouedkniss's terms of service and use responsibly.

## Disclaimer

This scraper is designed for research and analytics purposes. Users are responsible for ensuring their use complies with Ouedkniss's terms of service and applicable laws. The authors are not responsible for any misuse of this software.

## Contact

For questions, issues, or contributions, please open an issue on the repository.

---

**Built with ❤️ using Python, FastAPI, and MongoDB**
