from abc import ABC, abstractmethod
from models.listing import Listing

class BaseFilter(ABC):
    @abstractmethod
    def filter(self, listing: Listing) -> bool:
        """
        Filter a listing
        Returns True if listing passes (keep it)
        Returns False if listing fails (reject it)
        """
        pass