
import asyncio
import sys
import os
from pathlib import Path

# Add the project root to sys.path
project_root = str(Path(__file__).resolve().parent.parent)
sys.path.append(project_root)

# Mock logger to avoid import errors if logging config is complex
import logging
logging.basicConfig(level=logging.INFO)

try:
    from app.service.crawler.main import scrape_drug_web_advanced
except ImportError as e:
    print(f"Import Error: {e}")
    sys.exit(1)

async def main():
    keyword = "Paracetamol"
    print(f"--- Reproducing Issue for: {keyword} ---")
    
    try:
        # Try non-headless to match working script behavior
        result = await scrape_drug_web_advanced(keyword, headless=False)
        print("\n--- Result ---")
        print(result)
        
        if result.get("status") == "not_found":
            print("\n[FAIL] Drug not found.")
        elif not result.get("so_dang_ky") or result.get("so_dang_ky") == "Web Result (No SDK)":
             print("\n[FAIL] SDK is missing or invalid.")
        else:
             print("\n[SUCCESS] SDK found: ", result.get("so_dang_ky"))

    except Exception as e:
        print(f"\n[ERROR] Exception during scraping: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
