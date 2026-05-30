from abc import ABC, abstractmethod
from typing import List, Dict, Any
from curl_cffi import requests
import random
import time

class BaseScraper(ABC):
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.browser_config = config.get("browser", {})
        self.scraper_config = config.get("scraper", {})
        self.user_agents = self.browser_config.get("user_agents", [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        ])
        self.max_retries = self.scraper_config.get("max_retries", 3)
        self.delay_min = self.scraper_config.get("delay_min", 1.0)
        self.delay_max = self.scraper_config.get("delay_max", 3.0)

    @abstractmethod
    def search(self, query: str) -> List[Dict[str, Any]]:
        """
        Executes the search for the given query and returns a list of dictionaries.
        Each dictionary should represent a product with at least:
        - title
        - price
        - original_price
        - url
        - platform
        - image_url
        - rating
        """
        pass

    def get_headers(self) -> Dict[str, str]:
        return {
            "User-Agent": random.choice(self.user_agents),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1"
        }

    def _request_html(self, url: str, *, verify_ssl: bool = True) -> str:
        kwargs = {
            "headers": self.get_headers(),
            "timeout": 15,
            "impersonate": "chrome110",
        }
        if not verify_ssl:
            kwargs["verify"] = False
        response = requests.get(url, **kwargs)
        response.raise_for_status()
        return response.text

    def fetch_html(self, url: str) -> str:
        """
        Fetches the HTML content of the given URL with retries and delays.
        """
        retries = 0
        verify_ssl = True
        while retries < self.max_retries:
            try:
                # Add a random delay to mimic human behavior
                time.sleep(random.uniform(self.delay_min, self.delay_max))
                
                # Use impersonate to bypass TLS fingerprinting blocks
                return self._request_html(url, verify_ssl=verify_ssl)
            except Exception as e:
                err = str(e).lower()
                if verify_ssl and ("ssl" in err or "certificate" in err):
                    print(f"[{self.__class__.__name__}] SSL verify failed; retrying without certificate verification.")
                    verify_ssl = False
                    continue
                print(f"[{self.__class__.__name__}] Request failed for {url}: {e}")
                retries += 1
                if retries >= self.max_retries:
                    return ""
                time.sleep(self.scraper_config.get("retry_backoff", 2.0) * retries)
        return ""

    def clean_price(self, price_str: str) -> float:
        """
        Cleans a price string (e.g., '₹1,299.00') and returns a float.
        """
        if not price_str:
            return 0.0
        
        # Remove non-numeric characters except for the decimal point
        cleaned = ''.join(c for c in price_str if c.isdigit() or c == '.')
        
        # Handle cases where multiple decimal points might appear
        if cleaned.count('.') > 1:
            parts = cleaned.split('.')
            cleaned = parts[0] + '.' + ''.join(parts[1:])
            
        try:
            return float(cleaned)
        except ValueError:
            return 0.0
