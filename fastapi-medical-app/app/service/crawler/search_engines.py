"""
Multi-Engine Search Module - Based on solution_v03.py (Knowledge)
Provides search across Google, Bing, DuckDuckGo with human-like behavior.

Reference: knowledge for agent/solution_v03.py
DO NOT modify the knowledge source file.
"""
import asyncio
from typing import List, Dict, Tuple
from urllib.parse import urlparse, quote_plus
import logging

from .stealth_config import (
    human_pause, 
    human_scroll, 
    simulate_human_behavior,
    block_heavy_resources
)

logger = logging.getLogger(__name__)

# ======================================================
# CONFIGURATION (Extended from V03)
# ======================================================
GOTO_TIMEOUT = 45000  # 45 seconds
MAX_LINKS_DEFAULT = 10

ALLOWED_DOMAINS = [
    "trungtamthuoc.com",
    "thuocbietduoc.com.vn",
    "nhathuoclongchau.com.vn",
    "dichvucong.dav.gov.vn",
]


# ======================================================
# URL UTILITIES (from V03)
# ======================================================
def is_allowed_domain(url: str) -> bool:
    """Check if URL belongs to allowed domains."""
    try:
        netloc = urlparse(url).netloc.lower()
        return any(domain in netloc for domain in ALLOWED_DOMAINS)
    except Exception:
        return False


def clean_url(url: str) -> str:
    """Remove tracking parameters from URL."""
    if "#" in url:
        url = url.split("#")[0]
    if "?srsltid=" in url:
        url = url.split("?srsltid=")[0]
    return url


def is_detail_page(url: str) -> bool:
    """
    Check if URL looks like a drug detail page.
    Helps filter out search pages, category pages, etc.
    """
    url_lower = url.lower()
    
    # Exclude patterns (search/category pages)
    exclude_patterns = [
        '/search', '/drgsearch', '/category', '/danh-muc',
        '/tim-kiem', '/kết-quả', '/ketqua', '?q=', '?s='
    ]
    if any(pattern in url_lower for pattern in exclude_patterns):
        return False
    
    # Include patterns (detail pages)
    detail_patterns = [
        '/thuoc-', '/thuoc/', '/product/', '/san-pham/',
        '/detail/', '/chi-tiet/', 'products/detail'
    ]
    return any(pattern in url_lower for pattern in detail_patterns)


# ======================================================
# SEARCH ENGINE: GOOGLE (from V03)
# ======================================================
async def search_google(page, query: str, max_links: int = 10) -> List[str]:
    """
    Search Google with human-like behavior.
    
    Args:
        page: Playwright page object
        query: Search query
        max_links: Maximum links to return
        
    Returns:
        List of found URLs
    """
    found_links = []
    
    try:
        url = f"https://www.google.com/search?q={quote_plus(query)}&num=20&hl=vi"
        logger.info(f"[Google] Searching: {query}")
        
        await page.goto(url, timeout=GOTO_TIMEOUT, wait_until="domcontentloaded")
        await human_pause(1.5, 2.5)
        await human_scroll(page, "light")
        await human_pause(0.5, 1.0)
        
        # Multiple selector strategies for robustness
        selectors = [
            "div.g a[href]",
            "#search a[href]",
            "a[jsname='UWckNb']",  # New Google layout
        ]
        
        for selector in selectors:
            try:
                links = await page.query_selector_all(selector)
                if links:
                    break
            except:
                continue
        else:
            links = []
        
        for a in links:
            if len(found_links) >= max_links:
                break
                
            try:
                href = await a.get_attribute("href")
                if not href or "google" in href.lower():
                    continue
                
                href = clean_url(href)
                if is_allowed_domain(href) and href not in found_links:
                    if is_detail_page(href):
                        found_links.append(href)
                        logger.info(f"  [+] {href[:70]}")
            except:
                continue
        
        logger.info(f"[Google] Found {len(found_links)} links")
        
    except Exception as e:
        logger.error(f"[Google] Error: {str(e)[:80]}")
    
    return found_links


# ======================================================
# SEARCH ENGINE: BING (from V03)
# ======================================================
async def search_bing(page, query: str, max_links: int = 10) -> List[str]:
    """
    Search Bing with human-like behavior.
    """
    found_links = []
    
    try:
        url = f"https://www.bing.com/search?q={quote_plus(query)}&count=20"
        logger.info(f"[Bing] Searching: {query}")
        
        await page.goto(url, timeout=GOTO_TIMEOUT, wait_until="domcontentloaded")
        await human_pause(1.5, 2.5)
        await human_scroll(page, "light")
        await human_pause(0.5, 1.0)
        
        selectors = ["#b_results h2 a", ".b_algo h2 a", ".b_algo a"]
        
        for selector in selectors:
            try:
                links = await page.query_selector_all(selector)
                if links:
                    break
            except:
                continue
        else:
            links = []
        
        for a in links:
            if len(found_links) >= max_links:
                break
                
            try:
                href = await a.get_attribute("href")
                if not href or "bing" in href.lower() or "microsoft" in href.lower():
                    continue
                
                href = clean_url(href)
                if is_allowed_domain(href) and href not in found_links:
                    if is_detail_page(href):
                        found_links.append(href)
                        logger.info(f"  [+] {href[:70]}")
            except:
                continue
        
        logger.info(f"[Bing] Found {len(found_links)} links")
        
    except Exception as e:
        logger.error(f"[Bing] Error: {str(e)[:80]}")
    
    return found_links


# ======================================================
# SEARCH ENGINE: DUCKDUCKGO (from V03)
# ======================================================
async def search_duckduckgo(page, query: str, max_links: int = 10) -> List[str]:
    """
    Search DuckDuckGo HTML version (less detection).
    """
    found_links = []
    
    try:
        url = f"https://html.duckduckgo.com/html/?q={quote_plus(query)}"
        logger.info(f"[DDG] Searching: {query}")
        
        await page.goto(url, timeout=GOTO_TIMEOUT, wait_until="domcontentloaded")
        await human_pause(1.0, 2.0)
        
        links = await page.query_selector_all("a.result__a")
        
        for a in links:
            if len(found_links) >= max_links:
                break
                
            try:
                href = await a.get_attribute("href")
                if not href or "duckduckgo" in href.lower():
                    continue
                
                href = clean_url(href)
                if is_allowed_domain(href) and href not in found_links:
                    if is_detail_page(href):
                        found_links.append(href)
                        logger.info(f"  [+] {href[:70]}")
            except:
                continue
        
        logger.info(f"[DDG] Found {len(found_links)} links")
        
    except Exception as e:
        logger.error(f"[DDG] Error: {str(e)[:80]}")
    
    return found_links


# ======================================================
# MAIN: PARALLEL MULTI-ENGINE SEARCH
# ======================================================
async def search_all_engines(
    page, 
    query: str, 
    max_links: int = MAX_LINKS_DEFAULT,
    engines: List[str] = None
) -> Dict:
    """
    Search all engines in parallel and merge results.
    
    Args:
        page: Playwright page object
        query: Search query (drug name)
        max_links: Maximum total links to return
        engines: List of engines to use ["google", "bing", "duckduckgo"]
        
    Returns:
        Dict with:
        - links: List of unique URLs
        - engines_used: List of engines that returned results
        - search_time: Time taken
    """
    import time
    start_time = time.time()
    
    if engines is None:
        engines = ["google", "bing", "duckduckgo"]
    
    engine_funcs = {
        "google": search_google,
        "bing": search_bing,
        "duckduckgo": search_duckduckgo,
    }
    
    # Run engines in parallel (but sequentially on same page for stability)
    # Note: For true parallel, need separate pages/contexts
    all_links = []
    engines_with_results = []
    
    for engine_name in engines:
        if engine_name in engine_funcs:
            try:
                links = await engine_funcs[engine_name](page, query, max_links)
                if links:
                    engines_with_results.append(engine_name)
                    for link in links:
                        if link not in all_links:
                            all_links.append(link)
                            if len(all_links) >= max_links:
                                break
                
                # Short pause between engines
                await human_pause(0.3, 0.6)
                
            except Exception as e:
                logger.warning(f"[{engine_name}] Failed: {e}")
    
    elapsed = time.time() - start_time
    
    result = {
        "links": all_links[:max_links],
        "engines_used": engines_with_results,
        "search_time": round(elapsed, 2),
        "total_found": len(all_links),
    }
    
    logger.info(f"[MultiEngine] Total: {len(all_links)} links in {elapsed:.1f}s from {engines_with_results}")
    
    return result


async def search_drug_links(
    browser, 
    drug_name: str, 
    max_links: int = 10,
    query_variants: List[str] = None
) -> Dict:
    """
    High-level function to search for drug links using multiple engines.
    Creates its own stealth context.
    
    Args:
        browser: Playwright browser object
        drug_name: Name of the drug to search
        max_links: Maximum links to return
        query_variants: Optional list of query variants to try
        
    Returns:
        Dict with links and metadata
    """
    from .stealth_config import create_stealth_context, block_heavy_resources
    
    # Default query variants
    if query_variants is None:
        query_variants = [
            f"{drug_name} thuoc",
            drug_name,
        ]
    
    context = await create_stealth_context(browser)
    page = await context.new_page()
    
    # Optional: block heavy resources for speed
    # await page.route("**/*", block_heavy_resources)
    
    try:
        all_links = []
        engines_used = set()
        
        for query in query_variants:
            if len(all_links) >= max_links:
                break
                
            logger.info(f"[DrugSearch] Query variant: '{query}'")
            
            result = await search_all_engines(
                page, 
                query, 
                max_links=max_links - len(all_links)
            )
            
            for link in result.get("links", []):
                if link not in all_links:
                    all_links.append(link)
            
            engines_used.update(result.get("engines_used", []))
        
        return {
            "success": len(all_links) > 0,
            "links": all_links[:max_links],
            "engines_used": list(engines_used),
            "query_variants": query_variants,
        }
        
    finally:
        await context.close()
