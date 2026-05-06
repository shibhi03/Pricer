import sys
import json
sys.stdout.reconfigure(encoding='utf-8')
from bs4 import BeautifulSoup

with open("amazon_dump.html", "wb") as fw:
    from curl_cffi import requests as r
    ua = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
    resp = r.get("https://www.amazon.in/s?k=laptop",
                 headers={"User-Agent": ua, "Accept-Language": "en-US,en;q=0.5",
                          "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8"},
                 impersonate="chrome110")
    fw.write(resp.content)
    print("Amazon status:", resp.status_code)

with open("amazon_dump.html", encoding="utf-8", errors="replace") as f:
    soup = BeautifulSoup(f, "lxml")

items = soup.select("div[data-component-type='s-search-result']")
print(f"Amazon items: {len(items)}")
if items:
    item = items[0]
    title_elem = item.select_one("h2 a span")
    print("title via h2 a span:", title_elem.get_text(strip=True)[:80] if title_elem else "NOT FOUND")
    
    # Try other selectors
    for sel in ["h2 span", "h2", "span.a-size-medium", "span.a-text-normal"]:
        el = item.select_one(sel)
        if el:
            txt = el.get_text(strip=True)
            print(f"  [{sel}] = {txt[:60]}")
            break
