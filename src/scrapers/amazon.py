from bs4 import BeautifulSoup
from .base import BaseScraper
from src.utils.url_builder import build_url

class AmazonScraper(BaseScraper):
    def search(self, query: str):
        url = build_url("amazon", self.config, query)
        html = self.fetch_html(url)
        if not html:
            return []

        soup = BeautifulSoup(html, 'lxml')
        results = []
        limit = self.scraper_config.get("results_per_platform", 5)
        
        items = soup.select("div[data-component-type='s-search-result']")
        for item in items[:limit]:
            try:
                # Amazon updated their DOM — h2 a span may be empty, fall back to h2 span
                title_elem = item.select_one("h2 a span") or item.select_one("h2 span")
                title = title_elem.text.strip() if title_elem else "Unknown Title"
                
                price_elem = item.select_one("span.a-price-whole")
                price_str = price_elem.text.strip() if price_elem else "0"
                price = self.clean_price(price_str)
                
                orig_price_elem = item.select_one("span.a-text-price span.a-offscreen")
                orig_price_str = orig_price_elem.text.strip() if orig_price_elem else price_str
                original_price = self.clean_price(orig_price_str)
                
                link_elem = item.select_one("h2 a")
                product_url = "https://www.amazon.in" + link_elem['href'] if link_elem and 'href' in link_elem.attrs else url
                
                img_elem = item.select_one("img.s-image")
                image_url = img_elem['src'] if img_elem and 'src' in img_elem.attrs else ""
                
                rating_elem = item.select_one("span.a-icon-alt")
                rating = rating_elem.text.strip() if rating_elem else "No Rating"
                
                results.append({
                    "title": title,
                    "price": price,
                    "original_price": original_price,
                    "url": product_url,
                    "platform": "amazon",
                    "image_url": image_url,
                    "rating": rating
                })
            except Exception as e:
                print(f"[Amazon] Error parsing item: {e}")
                
        return results
