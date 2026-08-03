import os
import requests
import time
from urllib.parse import urlparse

# List of the 10 selected Groww AMC URLs
AMC_URLS = [
    "https://groww.in/mutual-funds/amc/nj-mutual-funds",
    "https://groww.in/mutual-funds/amc/abakkus-mutual-funds",
    "https://groww.in/mutual-funds/amc/choice-mutual-funds",
    "https://groww.in/mutual-funds/amc/the-wealth-company-mutual-funds",
    "https://groww.in/mutual-funds/amc/capitalmind-mutual-funds",
    "https://groww.in/mutual-funds/amc/jioblackrock-mutual-funds",
    "https://groww.in/mutual-funds/amc/unifi-mutual-funds",
    "https://groww.in/mutual-funds/amc/helios-mutual-funds",
    "https://groww.in/mutual-funds/amc/bajaj-finserv-mutual-funds",
    "https://groww.in/mutual-funds/amc/navi-mutual-funds",
]

RAW_DATA_DIR = "./data/raw"

def get_filename_from_url(url):
    """Extracts a readable filename from the URL."""
    path = urlparse(url).path
    # Example: '/mutual-funds/amc/nj-mutual-funds' -> 'nj-mutual-funds.html'
    basename = path.strip('/').split('/')[-1]
    if not basename:
        basename = "index"
    return f"{basename}.html"

def scrape_and_save():
    """Scrapes URLs and saves raw HTML locally."""
    if not os.path.exists(RAW_DATA_DIR):
        os.makedirs(RAW_DATA_DIR)
        print(f"Created directory: {RAW_DATA_DIR}")

    print("Starting Web Scraper (Task 2.1)...")
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }

    success_count = 0
    for url in AMC_URLS:
        filename = get_filename_from_url(url)
        filepath = os.path.join(RAW_DATA_DIR, filename)
        
        print(f"Fetching: {url}")
        try:
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(response.text)
                
            print(f"  -> Saved to {filepath}")
            success_count += 1
            
            # Be polite to the server
            time.sleep(1)
            
        except Exception as e:
            print(f"  -> Failed to scrape {url}: {e}")
            
    print(f"Scraping completed. {success_count}/{len(AMC_URLS)} URLs saved successfully.")

if __name__ == "__main__":
    scrape_and_save()
