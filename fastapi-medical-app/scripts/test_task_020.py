"""
Test script for Task 020 - Multi-Engine Search Integration
Tests the new search_engines and stealth_config modules.
"""
import asyncio
import sys
import os

# Add project to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from playwright.async_api import async_playwright

async def test_stealth_config():
    """Test stealth configuration imports and values"""
    print("\n" + "="*60)
    print("TEST 1: Stealth Configuration")
    print("="*60)
    
    from app.service.crawler.stealth_config import (
        BROWSER_ARGS,
        STEALTH_INIT_SCRIPT,
        USER_AGENTS,
        get_random_user_agent,
        human_pause,
    )
    
    print(f"✓ BROWSER_ARGS: {len(BROWSER_ARGS)} args loaded")
    print(f"✓ STEALTH_INIT_SCRIPT: {len(STEALTH_INIT_SCRIPT)} chars")
    print(f"✓ USER_AGENTS pool: {len(USER_AGENTS)} agents")
    
    # Test random UA
    ua1 = get_random_user_agent()
    ua2 = get_random_user_agent()
    print(f"✓ Random UA: {ua1[:50]}...")
    
    # Test human pause (short)
    await human_pause(0.1, 0.2)
    print("✓ human_pause works")
    
    return True


async def test_search_engines_module():
    """Test search engine utilities"""
    print("\n" + "="*60)
    print("TEST 2: Search Engines Module")
    print("="*60)
    
    from app.service.crawler.search_engines import (
        is_allowed_domain,
        clean_url,
        is_detail_page,
        ALLOWED_DOMAINS,
    )
    
    print(f"✓ ALLOWED_DOMAINS: {ALLOWED_DOMAINS}")
    
    # Test domain check
    assert is_allowed_domain("https://trungtamthuoc.com/thuoc/test") == True
    assert is_allowed_domain("https://random-site.com/test") == False
    print("✓ is_allowed_domain works")
    
    # Test URL cleaning
    cleaned = clean_url("https://example.com/page?srsltid=123#section")
    assert "srsltid" not in cleaned
    assert "#" not in cleaned
    print(f"✓ clean_url: {cleaned}")
    
    # Test detail page detection
    assert is_detail_page("https://thuocbietduoc.com.vn/thuoc-123") == True
    assert is_detail_page("https://thuocbietduoc.com.vn/search?q=test") == False
    print("✓ is_detail_page works")
    
    return True


async def test_multi_engine_search():
    """Test actual multi-engine search with a drug name"""
    print("\n" + "="*60)
    print("TEST 3: Multi-Engine Search (Live)")
    print("="*60)
    
    from app.service.crawler.search_engines import search_drug_links
    from app.service.crawler.stealth_config import BROWSER_ARGS
    
    drug_name = "Paracetamol 500mg"
    print(f"Searching for: '{drug_name}'")
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=BROWSER_ARGS
        )
        
        try:
            result = await search_drug_links(
                browser,
                drug_name,
                max_links=5,
                query_variants=[f"{drug_name} thuoc", drug_name]
            )
            
            print(f"\n✓ Success: {result.get('success')}")
            print(f"✓ Engines used: {result.get('engines_used')}")
            print(f"✓ Links found: {len(result.get('links', []))}")
            
            for i, link in enumerate(result.get("links", [])[:5], 1):
                print(f"   {i}. {link[:70]}...")
                
        finally:
            await browser.close()
    
    return True


async def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("TASK 020 VERIFICATION TESTS")
    print("="*60)
    
    try:
        # Unit tests
        await test_stealth_config()
        await test_search_engines_module()
        
        # Integration test (optional - takes time)
        run_live = input("\nRun live search test? (y/n): ").strip().lower()
        if run_live == 'y':
            await test_multi_engine_search()
        
        print("\n" + "="*60)
        print("✅ ALL TESTS PASSED!")
        print("="*60)
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
