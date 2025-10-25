from pydantic import BaseModel, Field
from typing import List, Dict, Any

class Document(BaseModel):
    """
    A Pydantic model for a document, useful for data validation and serialization.
    """
    id: str = Field(..., alias="_id")
    filename: str
    status: str
    kvps: Dict[str, Any] = {}