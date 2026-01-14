import asyncio
import os
import sys
from playwright.async_api import async_playwright, Page, BrowserContext, Browser

# Force ProactorEventLoop for Windows
if sys.platform == 'win32':
    try:
        if not isinstance(asyncio.get_event_loop_policy(), asyncio.WindowsProactorEventLoopPolicy):
            asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    except Exception:
        pass

class PlaywrightManager:
    """
    Playwright DOM Manager for Web Scraping.
    Singleton pattern. Based on the working solution in browser_mcp_agent.
    """
    def __init__(self, headless: bool = True):
        self.playwright = None
        self.browser: Browser = None
        self.context: BrowserContext = None
        self.page: Page = None
        self.headless = headless
        self._lock = asyncio.Lock()

    async def initialize(self):
        async with self._lock:
            if not self.playwright:
                self.playwright = await async_playwright().start()
                
                # Robust args for Docker and Bot Detection
                args = [
                    '--disable-blink-features=AutomationControlled',
                    '--start-maximized',
                    '--disable-infobars',
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-accelerated-2d-canvas',
                    '--disable-gpu',
                    '--window-position=0,0',
                ]
                
                self.browser = await self.playwright.chromium.launch(
                    headless=self.headless,
                    args=args,
                )
                
                self.context = await self.browser.new_context(
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                    viewport={"width": 1920, "height": 1080},
                    java_script_enabled=True,
                    ignore_https_errors=True
                )
                
                self.page = await self.context.new_page()

    async def get_dom_content(self, url: str) -> dict:
        """
        Navigates to URL and returns DOM content.
        Handles popups, timeouts, and dynamic loading.
        """
        if not self.playwright:
            await self.initialize()

        try:
            # 1. Access URL
            try:
                await self.page.goto(url, timeout=60000, wait_until='domcontentloaded')
            except Exception as e:
                print(f"Warning: navigation timeout/error for {url}: {e}")
            
            # 2. Wait for content to settle
            await self.page.wait_for_timeout(2000)

            # 3. Handle Popups
            popup_selectors = ['button[aria-label="Close"]', '.close-button', '.modal-close', '#close-modal']
            for selector in popup_selectors:
                try:
                    if await self.page.is_visible(selector):
                        await self.page.click(selector, timeout=1000)
                        await self.page.wait_for_timeout(500)
                except:
                    pass

            # 4. Extract Main Content
            content = ""
            for tag in ['main', 'article', 'body']:
                try:
                    if await self.page.locator(tag).first.count() > 0:
                        content = await self.page.inner_text(tag)
                        break
                except:
                    pass
            
            if not content:
                content = await self.page.inner_text("body")

            title = await self.page.title()
            
            # 5. Extract Valid Links
            links = await self.page.evaluate("""() => {
                return Array.from(document.querySelectorAll('a')).map(a => ({
                    text: a.innerText.trim(),
                    href: a.href
                })).filter(l => l.text && l.href && l.href.startsWith('http'));
            }""")
            
            return {
                "status": "success",
                "url": url,
                "title": title,
                "content": content,
                "links": links[:50],
                "length": len(content)
            }

        except Exception as e:
            return {
                "status": "error",
                "url": url,
                "error": str(e)
            }

    async def cleanup(self):
        if self.context:
            await self.context.close()
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()

# Singleton
playwright_manager = PlaywrightManager(headless=True)
