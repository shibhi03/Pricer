import re
import json
from .base import BaseScraper
from src.utils.url_builder import build_url

class MyntraScraper(BaseScraper):
    def search(self, query: str):
        url = build_url("myntra", self.config, query)
        html = self.fetch_html(url)
        if not html:
            return []

        results = []
        limit = self.scraper_config.get("results_per_platform", 5)

        # Myntra injects all product data into window.__myx JSON (verified May 2025)
        # We parse the JSON directly instead of scraping HTML elements
        start_marker = "window.__myx = {"
        start_pos = html.find(start_marker)
        if start_pos < 0:
            print("[Myntra] window.__myx not found in HTML")
            return []

        start_pos += len("window.__myx = ")
        brace_depth = 0
        end_pos = start_pos
        for idx, ch in enumerate(html[start_pos:], start=start_pos):
            if ch == "{":
                brace_depth += 1
            elif ch == "}":
                brace_depth -= 1
                if brace_depth == 0:
                    end_pos = idx + 1
                    break

        try:
            data = json.loads(html[start_pos:end_pos])
        except json.JSONDecodeError as e:
            print(f"[Myntra] JSON parse error: {e}")
            return []

        products = (data.get("searchData", {})
                       .get("results", {})
                       .get("products", []))

        for p in products[:limit]:
            try:
                brand = p.get("brand", "")
                name = p.get("productName", p.get("product", "Unknown"))
                title = f"{brand} {name}".strip() if brand else name

                price = float(p.get("price", 0))
                mrp = float(p.get("mrp", price))

                landing = p.get("landingPageUrl", "")
                product_url = f"https://www.myntra.com/{landing}" if landing else url

                image_url = p.get("searchImage", "")

                raw_rating = p.get("rating", 0)
                rating = str(round(float(raw_rating), 1)) if raw_rating else "No Rating"

                results.append({
                    "title": title,
                    "price": price,
                    "original_price": mrp,
                    "url": product_url,
                    "platform": "myntra",
                    "image_url": image_url,
                    "rating": rating
                })
            except Exception as e:
                print(f"[Myntra] Error parsing item: {e}")

        print(f"[Myntra] Found {len(results)} results")
        return results
