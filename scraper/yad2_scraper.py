import re
import urllib.parse
import random
from typing import List, Optional
from datetime import datetime

from scraper.base_scraper import BaseScraper
from models.listing import Listing


class Yad2Scraper(BaseScraper):
    def __init__(self):
        super().__init__()
        self.base_url = "https://www.yad2.co.il"
        self.search_url = "https://www.yad2.co.il/realestate/rent"

        # Enhanced headers to look more like a real browser
        self.headers.update({
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'he-IL,he;q=0.9,en-US;q=0.8,en;q=0.7',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Cache-Control': 'max-age=0',
            'DNT': '1',
        })

        # Load search parameters from filters.json
        self.criteria = self._load_search_criteria()

        self.logger.info(f"Yad2Scraper initialized with criteria: {self.criteria}")

    def _load_search_criteria(self) -> dict:
        """Load search criteria from filters.json"""
        try:
            import json
            with open('config/filters.json', 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            self.logger.error("filters.json not found, using defaults")
            return {
                "price_min": 2500,
                "price_max": 4000,
                "locations": ["חיפה"]
            }

    def _load_neighborhood_config(self) -> dict:
        """Load neighborhood configuration from config file"""
        try:
            import json
            with open('config/neighborhoods.json', 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            self.logger.warning("neighborhoods.json not found, using defaults")
            return {
                "haifa_areas": {
                    "בת גלים": 598,
                    "נווה שאנן": 642,
                    "רמות רמז": 637,
                    "רמות אלון": 635
                },
                "haifa_city_params": {
                    "topArea": 25,
                    "area": 5,
                    "city": 4000
                }
            }

    def _build_search_url(self) -> str:
        """Build Yad2 search URL with real parameters for city-wide search"""
        price_min = self.criteria.get("price_min", 2000)
        price_max = self.criteria.get("price_max", 5000)
        rooms_min = self.criteria.get("rooms_min", 1)
        rooms_max = self.criteria.get("rooms_max", 10)

        # Load city parameters from config
        config = self._load_neighborhood_config()
        city_params = config.get("haifa_city_params", {})

        # Base Yad2 parameters for Haifa
        base_params = {
            'minPrice': int(price_min),
            'maxPrice': int(price_max),
            'minRooms': rooms_min,
            'maxRooms': rooms_max,
            'topArea': city_params.get('topArea', 25),  # North District
            'area': city_params.get('area', 5),  # Haifa Metro Area
            'city': city_params.get('city', 4000),  # Haifa City
        }

        query_string = urllib.parse.urlencode(base_params)
        full_url = f"{self.search_url}?{query_string}"

        self.logger.info(f"Search URL: {full_url}")
        self.logger.info(f"Searching Haifa: {price_min}-{price_max}₪, {rooms_min}-{rooms_max} rooms (exact decimals)")
        return full_url

    def _build_neighborhood_urls(self) -> List[str]:
        """Build search URLs for specific neighborhoods"""
        price_min = self.criteria.get("price_min", 2000)
        price_max = self.criteria.get("price_max", 5000)
        rooms_min = self.criteria.get("rooms_min", 2)
        rooms_max = self.criteria.get("rooms_max", 4)

        # Load configuration
        config = self._load_neighborhood_config()
        neighborhood_map = config.get("haifa_areas", {})
        city_params = config.get("haifa_city_params", {})

        urls = []
        locations = self.criteria.get("locations", [])

        if not locations:
            # No specific neighborhoods - search entire Haifa
            self.logger.info("No specific locations configured, using city-wide search")
            return [self._build_search_url()]

        for location in locations:
            if location in neighborhood_map:
                params = {
                    'minPrice': int(price_min),
                    'maxPrice': int(price_max),
                    'minRooms': rooms_min,  # Exact decimal value
                    'maxRooms': rooms_max,  # Exact decimal value
                    'topArea': city_params.get('topArea', 25),
                    'area': city_params.get('area', 5),
                    'city': city_params.get('city', 4000),
                    'neighborhood': neighborhood_map[location],
                    'zoom': 14
                }

                query_string = urllib.parse.urlencode(params)
                url = f"{self.search_url}?{query_string}"
                urls.append(url)
                self.logger.info(
                    f"Added search URL for {location} (ID: {neighborhood_map[location]}) - {rooms_min}-{rooms_max} rooms")
            else:
                self.logger.warning(f"Unknown neighborhood: {location}. Available: {list(neighborhood_map.keys())}")

        if not urls:
            # Fallback to city-wide search if no valid neighborhoods
            self.logger.info("No valid neighborhoods found, using city-wide search")
            urls = [self._build_search_url()]

        return urls

    def _is_captcha_page(self, html_content: str) -> bool:
        """Check if the page is a CAPTCHA/bot detection page"""
        captcha_indicators = [
            "Are you for real",
            "אבטחת אתר",
            "h-captcha",
            "hcaptcha",
            "ShieldSquare",
            "robot_checkup"
        ]

        for indicator in captcha_indicators:
            if indicator in html_content:
                return True
        return False

    async def _human_delay(self, min_seconds: float = 1.0, max_seconds: float = 3.0):
        """Add random delay to mimic human behavior"""
        delay = random.uniform(min_seconds, max_seconds)
        self.logger.debug(f"Human delay: {delay:.2f} seconds")
        await self._polite_delay(delay)

    async def scrape(self) -> List[Listing]:
        """Main scraping method with multiple neighborhood support"""
        self.logger.info("Starting Yad2 scraping process")

        try:
            # Add initial delay to mimic human behavior
            await self._human_delay(2, 5)

            # Build search URLs for all neighborhoods
            search_urls = self._build_neighborhood_urls()
            all_listings = []

            self.logger.info(f"🔍 Searching {len(search_urls)} location(s)")

            # Search each neighborhood
            for i, search_url in enumerate(search_urls, 1):
                try:
                    self.logger.info(f"📍 Searching location {i}/{len(search_urls)}")
                    self.logger.debug(f"URL: {search_url}")

                    # Fetch the search results page
                    html_content = await self._fetch_page(search_url)
                    if not html_content:
                        self.logger.error(f"Failed to fetch search page {i}")
                        continue

                    # Check for CAPTCHA
                    if self._is_captcha_page(html_content):
                        self.logger.warning(f"🤖 CAPTCHA detected on search {i}! Yad2 blocked the request.")
                        self.logger.info("💡 Try again later or use different approach")
                        continue

                    # Parse HTML
                    soup = self._parse_html(html_content)
                    if not soup:
                        self.logger.error(f"Failed to parse HTML for search {i}")
                        continue

                    # Extract listings from the page
                    listings = await self._extract_listings(soup)

                    if listings:
                        all_listings.extend(listings)
                        self.logger.info(f"✅ Found {len(listings)} listings from location {i}")

                        # Show sample listing info for debugging
                        if listings:
                            sample = listings[0]
                            self.logger.debug(f"Sample: {sample.title[:50]} - {sample.price}₪ - {sample.location}")
                    else:
                        self.logger.info(f"📍 No listings found in location {i}")

                    # Human delay between searches
                    if i < len(search_urls):  # Don't delay after last search
                        await self._human_delay(3, 6)

                except Exception as e:
                    self.logger.error(f"Error searching location {i}: {e}")
                    continue

            # Remove duplicates based on ID
            unique_listings = []
            seen_ids = set()

            for listing in all_listings:
                if listing.id not in seen_ids:
                    unique_listings.append(listing)
                    seen_ids.add(listing.id)
                else:
                    self.logger.debug(f"Removed duplicate: {listing.title[:30]}...")

            self.logger.info(f"🎯 Found {len(unique_listings)} unique listings across all locations")
            return unique_listings

        except Exception as e:
            self.logger.error(f"Error in scrape(): {e}")
            return []

    async def _extract_listings(self, soup) -> List[Listing]:
        """Extract individual listings from the search results page"""
        listings = []

        # Look for all links that are actual rental listings (not projects/ads)
        all_links = soup.find_all('a', href=True)
        valid_listing_links = []

        for link in all_links:
            href = link.get('href')
            # Filter for ONLY individual rental listings, exclude projects and ads
            if href and '/realestate/item/' in href and 'project' not in href.lower():
                valid_listing_links.append(link)

        self.logger.info(f"🏠 Found {len(valid_listing_links)} individual rental listings (filtered out projects/ads)")

        # Show valid links for debugging
        for i, link in enumerate(valid_listing_links[:5]):
            self.logger.info(f"Valid Link {i}: {link.get('href')}")

        if not valid_listing_links:
            self.logger.warning("❌ No valid individual rental listings found")
            # Show what we DID find for debugging
            project_links = [l for l in all_links if l.get('href') and 'project' in l.get('href', '')]
            other_links = [l for l in all_links if l.get('href') and '/realestate/' in l.get('href', '')]
            self.logger.info(f"🏗️ Found {len(project_links)} project links (skipped)")
            self.logger.info(f"🔗 Found {len(other_links)} other real estate links")
            return []

        # Process each valid listing link
        for i, link in enumerate(valid_listing_links[:10]):
            try:
                # Extract the listing data from the link's parent element
                listing_element = link.find_parent() or link
                listing = await self._parse_single_listing(listing_element, link)

                if listing and self._is_valid_listing(listing):
                    listings.append(listing)
                    self.logger.info(
                        f"✅ Valid listing {i + 1}: {listing.title[:50]} - ₪{listing.price} - {listing.number_of_rooms} rooms")
                else:
                    self.logger.debug(f"❌ Invalid/incomplete listing {i + 1}")

                # Add random delay between processing
                await self._human_delay(0.5, 2.0)

            except Exception as e:
                self.logger.error(f"Error parsing listing {i + 1}: {e}")
                continue

        return listings

    def _is_valid_listing(self, listing: Listing) -> bool:
        """Check if a listing has minimum required data"""
        return (
                listing.title and len(listing.title) > 5 and
                listing.price > 0 and
                listing.number_of_rooms > 0 and
                listing.url and '/realestate/item/' in listing.url
        )

    def _debug_html_structure(self, soup):
        """Debug helper to understand HTML structure"""
        try:
            # Look for any div with Hebrew text
            divs_with_hebrew = soup.find_all('div', string=re.compile(r'[\u0590-\u05FF]'))
            if divs_with_hebrew:
                self.logger.info(f"Found {len(divs_with_hebrew)} divs with Hebrew text")
                for div in divs_with_hebrew[:3]:
                    self.logger.debug(f"Hebrew div: {div.get('class')} - {div.get_text()[:50]}")

            # Look for price indicators
            price_elements = soup.find_all(text=re.compile(r'[₪]'))
            if price_elements:
                self.logger.info(f"Found {len(price_elements)} elements with ₪ symbol")

            # Show a sample of the HTML structure
            self.logger.debug("Sample HTML structure:")
            for i, div in enumerate(soup.find_all('div')[:5]):
                self.logger.debug(f"Div {i}: class={div.get('class')} - {div.get_text()[:30]}")

        except Exception as e:
            self.logger.error(f"Error in debug: {e}")

    async def _parse_single_listing(self, element, link=None) -> Optional[Listing]:
        """Parse a single listing element and create a Listing object"""
        try:
            # Extract basic info
            title = self._extract_title(element)
            price = self._extract_price(element)
            rooms = self._extract_rooms(element)
            location = self._extract_location(element)
            description = self._extract_description(element)

            # Get URL from the provided link (more reliable)
            url = ""
            if link:
                href = link.get('href')
                if href:
                    if href.startswith('/'):
                        url = f"{self.base_url}{href}"
                    elif href.startswith('http'):
                        url = href

            # Fallback to element-based URL extraction if link URL failed
            if not url:
                url = self._extract_url(element)

            # Debug what we found
            self.logger.debug(f"Extracted - Title: {title[:30]}..., Price: {price}, Rooms: {rooms}, URL: {url[:50]}...")

            # Create listing object with extracted values
            listing = Listing(
                title=title or "No title found",
                number_of_rooms=rooms or 0.0,
                price=price or 0.0,
                location=location or "Unknown location",
                description=description or "",
                url=url or "",
                pets_allowed=None,
                source="yad2",
                contact_phone="",
                size_sqm=None,
                parking=None
            )

            return listing

        except Exception as e:
            self.logger.error(f"Error parsing single listing: {e}")
            return None

    def _extract_title(self, element) -> str:
        """Extract listing title with multiple fallback strategies"""
        try:
            # Try multiple possible title selectors
            title_selectors = [
                ('h1', {}),
                ('h2', {}),
                ('h3', {}),
                ('div', {'class': 'title'}),
                ('span', {'class': 'title'}),
                ('a', {'class': lambda x: x and 'title' in str(x).lower()}),
                ('div', {'class': lambda x: x and 'title' in str(x).lower()}),
            ]

            for tag, attrs in title_selectors:
                title_elem = element.find(tag, attrs)
                if title_elem:
                    title = self._clean_text(title_elem.get_text())
                    if title and len(title) > 5:  # Reasonable title length
                        return title

            # Fallback: look for any Hebrew text that might be a title
            for tag in ['h1', 'h2', 'h3', 'div', 'span', 'a']:
                elements = element.find_all(tag)
                for elem in elements:
                    text = elem.get_text().strip()
                    if text and re.search(r'[\u0590-\u05FF]', text) and len(text) > 10:
                        return self._clean_text(text)

            return ""
        except Exception as e:
            self.logger.error(f"Error extracting title: {e}")
            return ""

    def _extract_price(self, element) -> float:
        """Extract listing price"""
        try:
            # Get all text content from the element and its children
            all_text = element.get_text(separator=' ', strip=True)

            # Look for price patterns in Hebrew and English
            price_patterns = [
                r'(\d{1,2}[,.]?\d{3,4})\s*₪',  # 3,500₪ or 3.500₪
                r'₪\s*(\d{1,2}[,.]?\d{3,4})',  # ₪3,500
                r'(\d{1,2}[,.]?\d{3,4})\s*שקל',  # 3,500 שקל
                r'(\d{1,2}[,.]?\d{3,4})\s*ש"ח',  # 3,500 ש"ח
                r'מחיר[:\s]*(\d{1,2}[,.]?\d{3,4})',  # מחיר: 3500
                r'(\d{4,5})\s*(?:₪|שקל|ש"ח)',  # 3500₪
            ]

            for pattern in price_patterns:
                matches = re.findall(pattern, all_text)
                if matches:
                    # Clean the matched price (remove commas/dots used as thousands separators)
                    price_str = matches[0].replace(',', '').replace('.', '')
                    try:
                        price = float(price_str)
                        if 1000 <= price <= 5000:  # Reasonable price range
                            return price
                    except ValueError:
                        continue

            # Fallback: look for any 4-5 digit number that could be a price
            numbers = re.findall(r'\b(\d{4,5})\b', all_text)
            for num in numbers:
                price = float(num)
                if 1000 <= price <= 5000:
                    return price

            return 0.0
        except Exception as e:
            self.logger.error(f"Error extracting price: {e}")
            return 0.0

    def _extract_rooms(self, element) -> float:
        """Extract number of rooms with improved Hebrew pattern matching"""
        try:
            # Get all text content
            all_text = element.get_text(separator=' ', strip=True)

            # Hebrew room patterns
            room_patterns = [
                r'(\d+(?:\.\d+)?)\s*חדרים',  # 3 חדרים
                r'(\d+(?:\.\d+)?)\s*חד',  # 3 חד
                r'חדרים[:\s]*(\d+(?:\.\d+)?)',  # חדרים: 3
                r'(\d+(?:\.\d+)?)\s*ח[׳\']',  # 3 ח'
            ]

            for pattern in room_patterns:
                matches = re.findall(pattern, all_text)
                if matches:
                    try:
                        rooms = float(matches[0])
                        if 0.5 <= rooms <= 5:  # Reasonable room range
                            return rooms
                    except ValueError:
                        continue

            # Fallback: look for decimal numbers near room-related text
            if 'חדר' in all_text or 'חד' in all_text:
                # Look for patterns like "3.5", "2.5", etc.
                decimal_numbers = re.findall(r'\b(\d+\.5|\d+)\b', all_text)
                for num in decimal_numbers:
                    try:
                        rooms = float(num)
                        if 0.5 <= rooms <= 5:
                            return rooms
                    except ValueError:
                        continue

            return 0.0
        except Exception as e:
            self.logger.error(f"Error extracting rooms: {e}")
            return 0.0

    def _extract_location(self, element) -> str:
        """Extract listing location - only look for user's specific neighborhoods"""
        try:
            # Get all text and look for location patterns
            all_text = element.get_text(separator=' ', strip=True)

            # Get ONLY the neighborhoods from your filter criteria
            target_locations = self.criteria.get('locations', [])

            # Add "חיפה" as fallback for general listings
            search_areas = target_locations + ['חיפה']

            # Look for your specific areas in the text
            for area in search_areas:
                if area in all_text:
                    return area

            # Look for pattern "שכונת X" (neighborhood X)
            neighborhood_match = re.search(r'שכונת\s+([^,]+)', all_text)
            if neighborhood_match:
                neighborhood = neighborhood_match.group(1).strip()
                # Only return if it matches your target areas
                if neighborhood in target_locations:
                    return neighborhood

            return ""
        except Exception as e:
            self.logger.error(f"Error extracting location: {e}")
            return ""

    def _extract_description(self, element) -> str:
        """Extract listing description"""
        try:
            desc_selectors = [
                ('div', {'class': lambda x: x and 'description' in str(x).lower()}),
                ('p', {'class': lambda x: x and 'description' in str(x).lower()}),
                ('div', {'class': lambda x: x and 'content' in str(x).lower()}),
            ]

            for tag, attrs in desc_selectors:
                desc_elem = element.find(tag, attrs)
                if desc_elem:
                    description = self._clean_text(desc_elem.get_text())
                    if description and len(description) > 10:
                        return description

            return ""
        except Exception as e:
            self.logger.error(f"Error extracting description: {e}")
            return ""

    def _extract_url(self, element) -> str:
        """Extract listing URL with improved logic"""
        try:
            # Look for links that contain rental listing patterns
            link_patterns = [
                r'/realestate/rent/\d+',  # Main rental listing pattern
                r'/item/\d+',  # Alternative item pattern
                r'/rent-\d+',  # Another possible pattern
            ]

            # Find all links in the element
            links = element.find_all('a', href=True)

            for link in links:
                href = link.get('href')
                if href:
                    # Check if this looks like a listing URL
                    for pattern in link_patterns:
                        if re.search(pattern, href):
                            # Handle relative URLs
                            if href.startswith('/'):
                                return f"{self.base_url}{href}"
                            elif href.startswith('http'):
                                return href

            # Fallback: look for any link that might be a listing
            for link in links:
                href = link.get('href')
                if href and ('rent' in href.lower() or 'item' in href.lower()):
                    if href.startswith('/'):
                        return f"{self.base_url}{href}"
                    elif href.startswith('http'):
                        return href

            # Last resort: take the first meaningful link
            for link in links:
                href = link.get('href')
                if href and len(href) > 5 and not href.startswith('#'):
                    if href.startswith('/'):
                        return f"{self.base_url}{href}"
                    elif href.startswith('http'):
                        return href

            return ""
        except Exception as e:
            self.logger.error(f"Error extracting URL: {e}")
            return ""