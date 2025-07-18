import json
import os
from typing import List
from filters.base_filter import BaseFilter
from models.listing import Listing

class RuleFilter(BaseFilter):
    def __init__(self):
        self.criteria = self._load_filter_criteria()

    def _load_filter_criteria(self) -> dict:
        """Load filter criteria from config file"""
        try:
            with open('config/filters.json', 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            print("Warning: filters.json not found, using empty criteria")
            return {}

    def filter(self, listing: Listing) -> bool:
        """Apply rule-based filtering"""
        return (self._check_price(listing) and
                self._check_rooms(listing) and
                self._check_location(listing) and
                self._check_pets(listing) and
                self._check_exclude_keywords(listing))

    def _check_price(self, listing: Listing) -> bool:
        """Check if price is within range"""
        price_min = self.criteria.get('price_min', 0)
        price_max = self.criteria.get('price_max', float('inf'))

        return price_min <= listing.price <= price_max

    def _check_rooms(self, listing: Listing) -> bool:
        """Check if number of rooms is within range"""
        rooms_min = self.criteria.get('rooms_min', 0)
        rooms_max = self.criteria.get('rooms_max', float('inf'))

        return rooms_min <= listing.number_of_rooms <= rooms_max

    def _check_location(self, listing: Listing) -> bool:
        """Check if location matches allowed locations"""
        allowed_locations = self.criteria.get('locations', [])

        # If no locations specified, accept all
        if not allowed_locations:
            return True

        # Check if any allowed location appears in the listing location
        return any(location in listing.location for location in allowed_locations)

    def _check_pets(self, listing: Listing) -> bool:
        """Check pets policy"""
        pets_required = self.criteria.get('pets_allowed')

        # If no pet requirement specified, accept all
        if pets_required is None:
            return True

        # If pets required but listing doesn't allow pets
        if pets_required and listing.pets_allowed is False:
            return False

        return True

    def _check_exclude_keywords(self, listing: Listing) -> bool:
        """Check if listing contains any excluded keywords"""
        exclude_keywords = self.criteria.get('exclude_keywords', [])

        # If no exclude keywords specified, accept all
        if not exclude_keywords:
            return True

        # Use the method we already built in the Listing class!
        return not listing.matches_exclude_keywords(exclude_keywords)

    def __str__(self) -> str:
        """String representation of the filter criteria"""
        return f"RuleFilter{self.criteria}"