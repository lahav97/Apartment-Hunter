from datetime import datetime
from typing import Optional, List
import hashlib

class Listing:
    def __init__(self, title: str, number_of_rooms: float, price: float, location: str, 
             description: str, url: str, pets_allowed: Optional[bool], source: str, contact_phone: str,
                 size_sqm: Optional[float] = None, parking: Optional[bool] = None):
        self.title = title
        self.price = price
        self.number_of_rooms = number_of_rooms
        self.location = location
        self.description = description
        self.url = url
        self.pets_allowed = pets_allowed
        self.source = source
        self.scraped_at = datetime.now()
        self.id = self.generate_id()
        self.contact_phone = contact_phone
        self.size_sqm = size_sqm
        self.parking = parking

    def generate_id(self) -> str:
        content = f"{self.url}{self.title}{self.price}{self.number_of_rooms}"
        return hashlib.md5(content.encode('utf-8')).hexdigest()
    
    def matches_exclude_keywords(self, exclude_keywords: List[str]) -> bool:
        text_to_check = f"{self.title} {self.description}".lower()
        return any(keyword.lower() in text_to_check for keyword in exclude_keywords)
    