from typing import Dict, Any, List
from concurrent.futures import ThreadPoolExecutor, as_completed

from src.scrapers.amazon import AmazonScraper
from src.scrapers.flipkart import FlipkartScraper
from src.scrapers.meesho import MeeshoScraper
from src.scrapers.myntra import MyntraScraper
from src.scrapers.ajio import AjioScraper

from src.models.database import get_session_local, init_db
from src.models.product import Product, PriceHistory

class ScraperService:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.db_path = config.get("database", {}).get("path", "data/pricer.db")
        self.engine = init_db(self.db_path)
        self.SessionLocal = get_session_local(self.engine)
        
        self.scrapers = {}
        
        # Initialize enabled scrapers based on config
        platforms_config = config.get("platforms", {})
        
        if platforms_config.get("amazon", {}).get("enabled", False):
            self.scrapers["amazon"] = AmazonScraper(config)
            
        if platforms_config.get("flipkart", {}).get("enabled", False):
            self.scrapers["flipkart"] = FlipkartScraper(config)
            
        if platforms_config.get("meesho", {}).get("enabled", False):
            self.scrapers["meesho"] = MeeshoScraper(config)
            
        if platforms_config.get("myntra", {}).get("enabled", False):
            self.scrapers["myntra"] = MyntraScraper(config)
            
        if platforms_config.get("ajio", {}).get("enabled", False):
            self.scrapers["ajio"] = AjioScraper(config)

    def search(self, query: str) -> List[Dict[str, Any]]:
        """
        Executes search across all enabled platforms concurrently and saves results to DB.
        """
        all_results = []
        
        with ThreadPoolExecutor(max_workers=len(self.scrapers) or 1) as executor:
            future_to_platform = {
                executor.submit(scraper.search, query): name 
                for name, scraper in self.scrapers.items()
            }
            
            for future in as_completed(future_to_platform):
                platform = future_to_platform[future]
                try:
                    results = future.result()
                    all_results.extend(results)
                except Exception as exc:
                    print(f"[{platform.capitalize()}] Generated an exception: {exc}")
                    
        self._save_to_db(query, all_results)
        return all_results

    def _save_to_db(self, query: str, results: List[Dict[str, Any]]):
        """
        Saves the aggregated results to the database and tracks price history.
        """
        db = self.SessionLocal()
        try:
            for item in results:
                # Find if product already exists by URL
                product = db.query(Product).filter(Product.url == item["url"]).first()
                
                if not product:
                    product = Product(
                        search_query=query,
                        title=item["title"],
                        url=item["url"],
                        platform=item["platform"],
                        image_url=item.get("image_url", ""),
                        rating=item.get("rating", "No Rating")
                    )
                    db.add(product)
                    db.commit() # Commit to get product.id for PriceHistory
                    db.refresh(product)
                
                # Add historical price record
                price_history = PriceHistory(
                    product_id=product.id,
                    price=item["price"],
                    original_price=item.get("original_price", item["price"])
                )
                db.add(price_history)
            db.commit()
        except Exception as e:
            print(f"[DB Error] Failed to save results: {e}")
            db.rollback()
        finally:
            db.close()
