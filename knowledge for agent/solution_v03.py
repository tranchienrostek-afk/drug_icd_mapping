"""
Drug Link Finder - Solution V03 (BEST OF BOTH)
Combines:
- V01: Multiple search engines, direct URL, speed
- V02: Human behavior, persistent profile, anti-detection

Author: Combined approach
"""
from playwright.sync_api import sync_playwright, TimeoutError
from urllib.parse import urlparse, quote_plus
import time
import random
import logging
from typing import List, Dict
import sys
import os

sys.stdout.reconfigure(encoding='utf-8')

# ======================================================
# CONFIG
# ======================================================
PROFILE_DIR = "browser_profile"   # Persistent profile (from V02)
HEADLESS = True                   # Can run headless with stealth
GOTO_TIMEOUT = 45000
MAX_LINKS = 10

# Extended domain list (from V01)
ALLOWED_DOMAINS = [
    "trungtamthuoc.com",
    "thuocbietduoc.com.vn",
    "nhathuoclongchau.com.vn",
    #"vnras.com",
    #"pharmart.vn",
    #"drugbank.vn",
]

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("search_v03.log", encoding="utf-8", mode="w"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("DrugSearchV03")

# ======================================================
# HUMAN BEHAVIOR UTILS (from V02)
# ======================================================
def human_pause(a=0.3, b=0.8):
    """Shorter pauses for headless mode, still adds randomness"""
    time.sleep(random.uniform(a, b))

def human_scroll(page, intensity="light"):
    """Simulate human scrolling"""
    try:
        if intensity == "light":
            page.mouse.wheel(0, random.randint(200, 400))
        else:
            page.mouse.wheel(0, random.randint(400, 800))
    except:
        pass

def get_random_user_agent():
    """Rotate user agents"""
    agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
    ]
    return random.choice(agents)

# ======================================================
# UTILS
# ======================================================
def is_allowed_domain(url: str) -> bool:
    try:
        netloc = urlparse(url).netloc.lower()
        return any(domain in netloc for domain in ALLOWED_DOMAINS)
    except:
        return False

def clean_url(url: str) -> str:
    """Remove tracking parameters"""
    if "#" in url:
        url = url.split("#")[0]
    if "?srsltid=" in url:
        url = url.split("?srsltid=")[0]
    return url

# ======================================================
# SEARCH ENGINES (from V01, enhanced)
# ======================================================
def search_google(page, query: str, found_links: List[str]) -> int:
    """Search Google with human-like behavior"""
    try:
        url = f"https://www.google.com/search?q={quote_plus(query)}&num=20&hl=vi"
        logger.info(f"[Google] {query}")
        
        page.goto(url, timeout=GOTO_TIMEOUT, wait_until="domcontentloaded")
        human_pause(1.5, 2.5)
        human_scroll(page, "light")
        human_pause(0.5, 1.0)
        
        links = page.query_selector_all("div.g a[href], #search a[href]")
        count = 0
        
        for a in links:
            try:
                href = a.get_attribute("href")
                if not href or "google" in href.lower():
                    continue
                
                href = clean_url(href)
                if is_allowed_domain(href) and href not in found_links:
                    found_links.append(href)
                    count += 1
                    logger.info(f"  [+] {href[:70]}")
            except:
                continue
        
        logger.info(f"[Google] Found {count} links")
        return count
    except Exception as e:
        logger.error(f"[Google] Error: {str(e)[:50]}")
        return 0


def search_bing(page, query: str, found_links: List[str]) -> int:
    """Search Bing with human-like behavior"""
    try:
        url = f"https://www.bing.com/search?q={quote_plus(query)}&count=20"
        logger.info(f"[Bing] {query}")
        
        page.goto(url, timeout=GOTO_TIMEOUT, wait_until="domcontentloaded")
        human_pause(1.5, 2.5)
        human_scroll(page, "light")
        human_pause(0.5, 1.0)
        
        links = page.query_selector_all("#b_results h2 a, .b_algo h2 a")
        count = 0
        
        for a in links:
            try:
                href = a.get_attribute("href")
                if not href or "bing" in href.lower() or "microsoft" in href.lower():
                    continue
                
                href = clean_url(href)
                if is_allowed_domain(href) and href not in found_links:
                    found_links.append(href)
                    count += 1
                    logger.info(f"  [+] {href[:70]}")
            except:
                continue
        
        logger.info(f"[Bing] Found {count} links")
        return count
    except Exception as e:
        logger.error(f"[Bing] Error: {str(e)[:50]}")
        return 0


def search_duckduckgo(page, query: str, found_links: List[str]) -> int:
    """Search DuckDuckGo HTML version"""
    try:
        url = f"https://html.duckduckgo.com/html/?q={quote_plus(query)}"
        logger.info(f"[DDG] {query}")
        
        page.goto(url, timeout=GOTO_TIMEOUT, wait_until="domcontentloaded")
        human_pause(1.0, 2.0)
        
        links = page.query_selector_all("a.result__a")
        count = 0
        
        for a in links:
            try:
                href = a.get_attribute("href")
                if not href or "duckduckgo" in href.lower():
                    continue
                
                href = clean_url(href)
                if is_allowed_domain(href) and href not in found_links:
                    found_links.append(href)
                    count += 1
                    logger.info(f"  [+] {href[:70]}")
            except:
                continue
        
        logger.info(f"[DDG] Found {count} links")
        return count
    except Exception as e:
        logger.error(f"[DDG] Error: {str(e)[:50]}")
        return 0


# ======================================================
# MAIN SEARCH FUNCTION
# ======================================================
def search_drug_links(drug_name: str) -> List[str]:
    """
    Combined search using multiple engines with human-like behavior
    """
    found_links: List[str] = []
    
    # Query variations
    queries = [
        f"{drug_name} thuoc",
        f"{drug_name}",
    ]

    # Create profile directory if not exists
    if not os.path.exists(PROFILE_DIR):
        os.makedirs(PROFILE_DIR)

    with sync_playwright() as p:
        # Use persistent context (from V02) - stores cookies/history
        browser = p.chromium.launch_persistent_context(
            user_data_dir=PROFILE_DIR,
            headless=HEADLESS,
            viewport={"width": 1920, "height": 1080},
            locale="vi-VN",
            timezone_id="Asia/Ho_Chi_Minh",
            user_agent=get_random_user_agent(),
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
                "--disable-dev-shm-usage",
            ]
        )
        
        # Stealth injection
        browser.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
            window.chrome = {runtime: {}};
        """)
        
        page = browser.new_page()
        
        logger.info(f"\n{'='*60}")
        logger.info(f"SEARCHING: {drug_name}")
        logger.info(f"{'='*60}")
        
        for query in queries:
            if len(found_links) >= MAX_LINKS:
                logger.info(f"Reached {MAX_LINKS} links, stopping")
                break
            
            logger.info(f"\n--- Query: {query} ---")
            
            # Google (most reliable)
            search_google(page, query, found_links)
            human_pause(0.3, 0.6)
            
            # Bing
            search_bing(page, query, found_links)
            human_pause(0.3, 0.6)
            
            # DuckDuckGo
            search_duckduckgo(page, query, found_links)
            human_pause(0.3, 0.6)
        
        browser.close()
    
    return found_links


# ======================================================
# MAIN
# ======================================================
if __name__ == "__main__":
    # Support command line argument
    if len(sys.argv) > 1:
        drug_name = " ".join(sys.argv[1:]).strip()
    else:
        drug_name = "Berodual 200 liều (xịt) - 10ml",
    
    print(f"\n{'='*60}")
    print(f"[SEARCH] Drug: {drug_name}")
    print(f"{'='*60}\n")
    
    start_time = time.time()
    results = search_drug_links(drug_name)
    elapsed = time.time() - start_time
    
    print(f"\n{'='*60}")
    print(f"[RESULT] Found {len(results)} unique links in {elapsed:.1f}s")
    print(f"{'='*60}")
    
    if results:
        for i, link in enumerate(results, 1):
            print(f"  {i}. {link}")
    else:
        print("  [X] No links found")
    
    print(f"\nLog saved to: search_v03.log")
