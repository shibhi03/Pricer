import os
import time
from bs4 import BeautifulSoup
from .base import BaseScraper
from src.utils.url_builder import build_url

class MeeshoScraper(BaseScraper):
    def search(self, query: str):
        """
        Meesho is fully client-side rendered — product cards are not in the initial HTML.
        We use Selenium with headless Chrome to wait for the JS to inject the product cards.
        """
        url = build_url("meesho", self.config, query)
        limit = self.scraper_config.get("results_per_platform", 5)
        
        try:
            from selenium import webdriver
            from selenium.webdriver.chrome.options import Options
            from selenium.webdriver.common.by import By
            from selenium.webdriver.support.ui import WebDriverWait
            from selenium.webdriver.support import expected_conditions as EC
            from selenium.common.exceptions import SessionNotCreatedException
            from src.core.driver import _get_chrome_service, apply_chrome_runtime
        except ImportError:
            print("[Meesho] Selenium not installed. Skipping.")
            return []

        options = apply_chrome_runtime(Options())
        options.add_argument("--headless=new")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--window-size=1920,1080")
        options.add_argument(f"--user-agent={self.user_agents[0]}")
        # Disable automation flags to avoid detection
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option("useAutomationExtension", False)
        options.add_argument("--disable-blink-features=AutomationControlled")

        driver = None
        results = []
        try:
            service = _get_chrome_service(self.config)
            try:
                driver = webdriver.Chrome(service=service, options=options)
            except (OSError, SessionNotCreatedException) as e:
                print(f"[Meesho] ChromeDriver failed ({e}). Retrying with latest driver.")
                service = _get_chrome_service(self.config, use_cache_only=True)
                driver = webdriver.Chrome(service=service, options=options)
            driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
                "source": "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
            })
            driver.get(url)
            
            # Wait for product cards to appear
            wait = WebDriverWait(driver, 15)
            # Meesho product cards are in divs with data-testid or specific class patterns
            try:
                wait.until(EC.presence_of_element_located(
                    (By.CSS_SELECTOR, "div[data-testid='product-container'], div.sc-dkzDqf, a[data-testid='product-card']")
                ))
            except Exception:
                # Fallback: just wait a few seconds for JS to render
                time.sleep(5)
            
            html = driver.page_source
            soup = BeautifulSoup(html, "lxml")
            
            # Meesho product cards (verified structure — each product is in an <a> or div with href)
            # Look for product card wrappers
            cards = (
                soup.select("div[data-testid='product-container']") or
                soup.select("a[data-testid='product-card']") or
                soup.select("div.sc-dkzDqf") or
                soup.select("div.NewProductCardstyled__CardStyled-sc-6y2tys-0")
            )
            
            # Fallback: find all links pointing to product pages
            if not cards:
                cards = [a for a in soup.find_all("a", href=True)
                         if "/p/" in a.get("href", "") or "/product/" in a.get("href", "")]
            
            count = 0
            for card in cards:
                if count >= limit:
                    break
                try:
                    link_elem = card if card.name == "a" else card.find("a", href=True)
                    href = link_elem.get("href", "") if link_elem else ""
                    product_url = ("https://www.meesho.com" + href
                                   if href.startswith("/") else href) if href else url
                    
                    # Title — look for <p> tags inside the card
                    title_elem = (card.select_one("p[class*='Title']") or
                                  card.select_one("p[class*='Name']") or
                                  card.find("p"))
                    title = title_elem.get_text(strip=True) if title_elem else "Unknown Title"
                    
                    # Price — look for <h5> or <p> with rupee symbol
                    price_elem = (card.select_one("h5[class*='Price']") or
                                  card.find("h5") or
                                  card.find(string=lambda s: s and "₹" in s))
                    price_str = (price_elem.get_text(strip=True) if hasattr(price_elem, "get_text")
                                 else str(price_elem)) if price_elem else "0"
                    price = self.clean_price(price_str)
                    
                    img_elem = card.find("img")
                    image_url = img_elem.get("src", "") if img_elem else ""
                    
                    if not title or title == "Unknown Title":
                        continue
                    
                    results.append({
                        "title": title,
                        "price": price,
                        "original_price": price,
                        "url": product_url,
                        "platform": "meesho",
                        "image_url": image_url,
                        "rating": "No Rating"
                    })
                    count += 1
                except Exception as e:
                    print(f"[Meesho] Error parsing card: {e}")
        
        except Exception as e:
            print(f"[Meesho] Selenium error: {e}")
        finally:
            if driver:
                driver.quit()
        
        print(f"[Meesho] Found {len(results)} results")
        return results
