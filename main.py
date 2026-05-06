import argparse
import sys
import os
import subprocess

from src.core.config_loader import load_config
from src.services.scrapper_service import ScraperService

def main():
    parser = argparse.ArgumentParser(description="Pricer E-commerce Scraper")
    parser.add_argument("--query", type=str, help="Search query to run scraper from CLI")
    parser.add_argument("--ui", action="store_true", help="Launch the Streamlit UI")
    
    args = parser.parse_args()
    
    # If no args provided, default to starting UI
    if not args.query and not args.ui:
        print("Starting Streamlit UI...")
        subprocess.run([sys.executable, "-m", "streamlit", "run", "ui/app.py"])
        return

    if args.ui:
        print("Starting Streamlit UI...")
        subprocess.run([sys.executable, "-m", "streamlit", "run", "ui/app.py"])
        return
        
    if args.query:
        print(f"Running scraper for query: '{args.query}'")
        config = load_config()
        service = ScraperService(config)
        results = service.search(args.query)
        
        print("\n--- Scraper Results ---")
        for item in results:
            print(f"[{item['platform'].upper()}] {item['title'][:50]}... | Price: {item['price']}")
        print(f"\nTotal items found: {len(results)}")
        print("Results saved to database.")

if __name__ == "__main__":
    main()
