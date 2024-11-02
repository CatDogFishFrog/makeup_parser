from pydantic import BaseModel, HttpUrl
from typing import List, Optional

class ProductVariant(BaseModel):
    title: str
    price: int
    eu_stock: bool

class Product(BaseModel):
    name: str
    url: HttpUrl
    variants: List[ProductVariant] = []

class ProcessingResult(BaseModel):
    success: bool
    message: Optional[str] = None
    error: Optional[str] = None