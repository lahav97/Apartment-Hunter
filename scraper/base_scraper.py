from abc import ABC, abstractmethod
from typing import List
import aiohttp
import asyncio
import logging
from datetime import datetime

from models.listing import Listing


class BaseScraper(ABC):
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.session = None
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }

    @abstractmethod
    async def scrape(self) -> List[Listing]:
        """Scrape listings from the source - must be implemented by child classes"""
        pass

    async def __aenter__(self):
        """Async context manager entry - creates HTTP session"""
        self.session = aiohttp.ClientSession(headers=self.headers)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit - closes HTTP session"""
        if self.session:
            await self.session.close()

    async def _fetch_page(self, url: str, timeout: int = 10) -> str:
        """Fetch a web page and return its HTML content"""
        try:
            if not self.session:
                self.session = aiohttp.ClientSession(headers=self.headers)

            self.logger.info(f"Fetching: {url}")

            async with self.session.get(url, timeout=timeout) as response:
                if response.status == 200:
                    content = await response.text()
                    self.logger.info(f"Successfully fetched {len(content)} characters")
                    return content
                else:
                    self.logger.error(f"HTTP {response.status} for {url}")
                    return ""

        except asyncio.TimeoutError:
            self.logger.error(f"Timeout fetching {url}")
            return ""
        except Exception as e:
            self.logger.error(f"Error fetching {url}: {e}")
            return ""

    def _parse_html(self, html_content: str):
        """Parse HTML content with BeautifulSoup"""
        try:
            from bs4 import BeautifulSoup
            return BeautifulSoup(html_content, 'html.parser')
        except ImportError:
            self.logger.error("BeautifulSoup4 not installed. Run: pip install beautifulsoup4")
            return None
        except Exception as e:
            self.logger.error(f"Error parsing HTML: {e}")
            return None

    async def _polite_delay(self, seconds: float = 1.0):
        """Add delay between requests to be polite to websites"""
        self.logger.debug(f"Waiting {seconds} seconds...")
        await asyncio.sleep(seconds)

    def _clean_text(self, text: str) -> str:
        """Clean and normalize text"""
        if not text:
            return ""

        # Remove extra whitespace and newlines
        cleaned = " ".join(text.strip().split())
        return cleaned

    def __str__(self) -> str:
        """String representation of the scraper"""
        return f"{self.__class__.__name__}(session={'active' if self.session else 'inactive'})"

    async def close(self):
        """Manually close the session if needed"""
        if self.session:
            await self.session.close()
            self.session = None
            self.logger.info("Session closed")