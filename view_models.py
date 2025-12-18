from typing import Optional
from pydantic import BaseModel, Field

class ItenaryFilters(BaseModel):
    additional_prompt: Optional[str] = "None"
    days_count: Optional[int] = 3
    region: Optional[str] = "Any & All"
    deity: Optional[str] = "Any & All"
    yatra_specifics: Optional[str] = "Any & All"
    pace: Optional[str] = "Comfortable & Easy"
    transport_preference: Optional[str] = "Any & All"
    specific_interests: Optional[str] = "Nothing specific, exlplore all"