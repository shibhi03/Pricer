from bs4 import BeautifulSoup
from .base import BaseScraper
from src.utils.url_builder import build_url

class FlipkartScraper(BaseScraper):
    def search(self, query: str):
        url = build_url("flipkart", self.config, query)
        html = self.fetch_html(url)
        if not html:
            return []

        soup = BeautifulSoup(html, 'lxml')
        results = []
        limit = self.scraper_config.get("results_per_platform", 5)

        # Products are in div[data-id] cards (verified May 2025)
        items = soup.select("div[data-id]")
        count = 0

        for item in items:
            if count >= limit:
                break
            try:
                # Title: comes from the product image alt text
                img_elem = item.select_one("img")
                title = img_elem['alt'].strip() if img_elem and img_elem.get('alt') else "Unknown Title"

                # URL: first anchor in the card
                link_elem = item.select_one("a[href]")
                product_url = ("https://www.flipkart.com" + link_elem['href']
                               if link_elem and 'href' in link_elem.attrs else url)

                # Price selectors (verified May 2025): hZ3P6w = discounted, kRYCnD = original
                price_elem = item.select_one("div.hZ3P6w")
                price_str = price_elem.get_text(strip=True) if price_elem else "0"
                price = self.clean_price(price_str)

                orig_price_elem = item.select_one("div.kRYCnD")
                orig_price_str = orig_price_elem.get_text(strip=True) if orig_price_elem else price_str
                original_price = self.clean_price(orig_price_str)

                # Image
                image_url = img_elem['src'] if img_elem and 'src' in img_elem.attrs else ""

                # Rating: MKiFS6 div or CjyrHS span (verified May 2025)
                rating_elem = item.select_one("div.MKiFS6") or item.select_one("span.CjyrHS")
                rating = rating_elem.get_text(strip=True) if rating_elem else "No Rating"

                if price == 0 and original_price == 0:
                    continue  # Skip cards without price (ads/banners)

                results.append({
                    "title": title,
                    "price": price,
                    "original_price": original_price,
                    "url": product_url,
                    "platform": "flipkart",
                    "image_url": image_url,
                    "rating": rating
                })
                count += 1
            except Exception as e:
                print(f"[Flipkart] Error parsing item: {e}")

        print(f"[Flipkart] Found {len(results)} results")
        return results
