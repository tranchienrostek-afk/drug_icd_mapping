"""
Google Search Service for finding drug detail pages.
Uses Google's site-specific search to find direct URLs quickly.
"""
import logging
from typing import Optional, List
from googlesearch import search

logger = logging.getLogger(__name__)

class GoogleSearchService:
    """
    Service to find drug detail pages using Google Search.
    Much faster and more accurate than internal site search.
    """
    
    def __init__(self, domain: str = "thuocbietduoc.com.vn"):
        """
        Initialize Google Search Service.
        
        Args:
            domain: Target domain to search within
        """
        self.domain = domain
        
    def find_drug_url(self, drug_name: str, max_results: int = 5) -> Optional[str]:
        """
        Find direct URL to drug detail page using Google Search.
        
        Args:
            drug_name: Name of the drug to search
            max_results: Maximum number of results to check
            
        Returns:
            Direct URL to drug page or None if not found
        """
        try:
            # Construct Google search query: site:domain.com drug_name
            query = f"site:{self.domain} {drug_name}"
            logger.info(f"[GoogleSearch] Query: '{query}'")
            
            # Search and filter results
            for idx, url in enumerate(search(query, num_results=max_results, lang='vi')):
                logger.info(f"[GoogleSearch] Result {idx+1}: {url}")
                
                # Filter: Must be from target domain and look like detail page
                if self.domain in url and self._is_detail_page(url):
                    logger.info(f"[GoogleSearch] ✓ Selected: {url}")
                    return url
                    
            logger.warning(f"[GoogleSearch] No valid URL found for '{drug_name}'")
            return None
            
        except Exception as e:
            logger.error(f"[GoogleSearch] Error: {e}")
            return None
    
    def _is_detail_page(self, url: str) -> bool:
        """
        Check if URL looks like a drug detail page.
        
        Args:
            url: URL to check
            
        Returns:
            True if URL appears to be a detail page
        """
        # Heuristic: Detail pages usually have /thuoc-{id}/ or /thuoc/{name}
        detail_patterns = ['/thuoc-', '/thuoc/']
        
        # Exclude: Search pages, category pages, etc.
        exclude_patterns = ['/search', '/drgsearch', '/category', '/danh-muc']
        
        url_lower = url.lower()
        
        # Check exclusions first
        if any(pattern in url_lower for pattern in exclude_patterns):
            return False
            
        # Check if it matches detail patterns
        return any(pattern in url_lower for pattern in detail_patterns)
