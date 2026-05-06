import json
import re
from .base import BaseScraper
from src.utils.url_builder import build_url

class AjioScraper(BaseScraper):
    def search(self, query: str):
        url = build_url("ajio", self.config, query)
        html = self.fetch_html(url)
        if not html:
            return []

        results = []
        limit = self.scraper_config.get("results_per_platform", 5)

        # Ajio injects products into window.__PRELOADED_STATE__ (verified May 2025)
        # Products are in state.grid.entities (a dict keyed by product code)
        start_marker = "window.__PRELOADED_STATE__ = {"
        start_pos = html.find(start_marker)
        if start_pos < 0:
            print("[Ajio] __PRELOADED_STATE__ not found in HTML")
            return []

        start_pos += len("window.__PRELOADED_STATE__ = ")
        # Use brace counting to find the exact end of the JSON object
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
            print(f"[Ajio] JSON parse error: {e}")
            return []

        entities = data.get("grid", {}).get("entities", {})
        if not entities:
            print("[Ajio] No products in grid.entities")
            return []

        for code, product in list(entities.items())[:limit]:
            try:
                brand_data = product.get("fnlColorVariantData", {})
                brand = brand_data.get("brandName", "")
                name = product.get("name", "Unknown")
                title = f"{brand} {name}".strip() if brand else name

                # price = current selling price, offerPrice = after coupon (may be 0)
                price = float(product.get("price", 0))
                original_price = float(product.get("wasPriceData", {}).get("price", price) or price)

                product_url = "https://www.ajio.com" + product.get("url", "")

                images = product.get("images", [])
                image_url = images[0].get("url", "") if images else ""

                rating = str(product.get("averageRating", "No Rating"))

                results.append({
                    "title": title,
                    "price": price,
                    "original_price": original_price,
                    "url": product_url,
                    "platform": "ajio",
                    "image_url": image_url,
                    "rating": rating
                })
            except Exception as e:
                print(f"[Ajio] Error parsing item: {e}")

        print(f"[Ajio] Found {len(results)} results")
        return results
