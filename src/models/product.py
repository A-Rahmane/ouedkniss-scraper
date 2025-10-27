"""
Data models for Ouedkniss products.
"""
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Optional, Any
from datetime import datetime


@dataclass
class SellerInfo:
    """Seller information."""
    
    name: str
    phone: Optional[str] = None
    email: Optional[str] = None
    address: Optional[str] = None
    location: Optional[Dict[str, str]] = None


@dataclass
class QuestionAnswer:
    """Question and answer pair."""
    
    question: str
    answer: Optional[str]
    asked_date: Optional[str] = None
    answered_date: Optional[str] = None


@dataclass
class Product:
    """Product data model."""
    
    # Identifiers
    product_id: str
    url: str
    
    # Basic Information
    title: str
    category: str
    subcategories: List[str]
    
    # Pricing
    price: Optional[float] = None
    currency: str = "DZD"
    negotiable: bool = False
    
    # Description
    description: Optional[str] = None
    
    # Specifications
    specifications: Dict[str, Any] = field(default_factory=dict)
    
    # Media
    images: List[str] = field(default_factory=list)
    
    # Seller Information
    seller: Optional[SellerInfo] = None
    
    # Q&A
    questions_answers: List[QuestionAnswer] = field(default_factory=list)
    
    # Metadata
    scraped_at: datetime = field(default_factory=datetime.utcnow)
    last_updated: Optional[str] = None
    views: Optional[int] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert product to dictionary."""
        data = asdict(self)
        data['scraped_at'] = self.scraped_at.isoformat()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Product':
        """Create Product from dictionary."""
        if isinstance(data.get('scraped_at'), str):
            data['scraped_at'] = datetime.fromisoformat(data['scraped_at'])
        
        if data.get('seller') and isinstance(data['seller'], dict):
            data['seller'] = SellerInfo(**data['seller'])
        
        if data.get('questions_answers'):
            data['questions_answers'] = [
                QuestionAnswer(**qa) if isinstance(qa, dict) else qa
                for qa in data['questions_answers']
            ]
        
        return cls(**data)
