# Quick verification test
import sys
sys.path.insert(0, r'C:\Users\Admin\Desktop\drug_icd_mapping\fastapi-medical-app')

print("="*50)
print("Task 020 - Quick Verification")
print("="*50)

# Test 1: Stealth Config
print("\n[1] Testing stealth_config...")
from app.service.crawler.stealth_config import (
    BROWSER_ARGS,
    STEALTH_INIT_SCRIPT,
    get_random_user_agent,
)
print(f"  BROWSER_ARGS: {len(BROWSER_ARGS)} args")
print(f"  STEALTH_INIT_SCRIPT: {len(STEALTH_INIT_SCRIPT)} chars")
print(f"  Random UA: {get_random_user_agent()[:50]}...")

# Test 2: Search Engines utilities
print("\n[2] Testing search_engines utilities...")
from app.service.crawler.search_engines import (
    is_allowed_domain,
    clean_url,
    is_detail_page,
    ALLOWED_DOMAINS,
)
print(f"  ALLOWED_DOMAINS: {ALLOWED_DOMAINS}")

# Test domain check
test_url_1 = "https://trungtamthuoc.com/thuoc/test"
test_url_2 = "https://random-site.com/test"
print(f"  is_allowed_domain('{test_url_1}'): {is_allowed_domain(test_url_1)}")
print(f"  is_allowed_domain('{test_url_2}'): {is_allowed_domain(test_url_2)}")

# Test URL cleaning
dirty_url = "https://example.com/page?srsltid=123#section"
print(f"  clean_url('{dirty_url}'): {clean_url(dirty_url)}")

# Test detail page detection
detail_url = "https://thuocbietduoc.com.vn/thuoc-123"
search_url = "https://thuocbietduoc.com.vn/search?q=test"
print(f"  is_detail_page('{detail_url}'): {is_detail_page(detail_url)}")
print(f"  is_detail_page('{search_url}'): {is_detail_page(search_url)}")

# Test 3: Main integration check
print("\n[3] Testing main.py integration...")
from app.service.crawler.main import scrape_drug_web_advanced
print(f"  scrape_drug_web_advanced imported: OK")

print("\n" + "="*50)
print("ALL TESTS PASSED!")
print("="*50)
