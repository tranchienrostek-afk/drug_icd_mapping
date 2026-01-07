
import asyncio
from playwright.async_api import async_playwright

async def debug_long_chau():
    async with async_playwright() as p:
        # Launch browser with headless=False to see the UI
        browser = await p.chromium.launch(headless=False)
        
        # Create context with SAME configuration as the actual scraper
        context = await browser.new_context(
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            viewport={'width': 1920, 'height': 1080},
            permissions=['geolocation', 'notifications']
        )
        
        page = await context.new_page()
        
        print("Navigating to Nha Thuoc Long Chau...")
        await page.goto("https://nhathuoclongchau.com.vn")
        
        # Block images/css like the real scraper to see if that breaks layout (Optional, commented out for now to see full UI first)
        # await page.route("**/*.{png,jpg,jpeg,gif,webp,svg,css,woff,woff2,ttf,eot,mp4,mp3}", lambda route: route.abort())

        print("Browser is OPEN. You can now use F12 to inspect elements.")
        print("The script is paused. Click the 'Resume' button in the Playwright Inspector window or press Close to stop.")
        
        # This will open the Playwright Inspector overlay and pause execution
        await page.pause() 
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(debug_long_chau())
