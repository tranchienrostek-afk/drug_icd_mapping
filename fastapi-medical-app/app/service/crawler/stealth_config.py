"""
Stealth Configuration Module - Based on solution_v03.py (Knowledge)
Provides anti-detection settings and human-like behavior utilities.

Reference: knowledge for agent/solution_v03.py
DO NOT modify the knowledge source file.
"""
import random
import asyncio
from typing import List

# ======================================================
# BROWSER ARGS (from V03)
# ======================================================
BROWSER_ARGS = [
    "--disable-blink-features=AutomationControlled",
    "--no-sandbox",
    "--disable-setuid-sandbox",
    "--disable-dev-shm-usage",
    "--disable-gpu",
]

# ======================================================
# STEALTH INJECTION SCRIPT (from V03)
# Hides automation markers from websites
# ======================================================
STEALTH_INIT_SCRIPT = """
    // Hide webdriver property
    Object.defineProperty(navigator, 'webdriver', {
        get: () => undefined
    });
    
    // Mock chrome runtime
    window.chrome = {
        runtime: {}
    };
    
    // Override permissions API
    const originalQuery = window.navigator.permissions.query;
    window.navigator.permissions.query = (parameters) => (
        parameters.name === 'notifications' ?
            Promise.resolve({ state: Notification.permission }) :
            originalQuery(parameters)
    );
    
    // Add plugins (real browsers have these)
    Object.defineProperty(navigator, 'plugins', {
        get: () => [1, 2, 3, 4, 5],
    });
    
    // Add languages
    Object.defineProperty(navigator, 'languages', {
        get: () => ['vi-VN', 'vi', 'en-US', 'en'],
    });
"""

# ======================================================
# USER AGENT ROTATION (from V03)
# ======================================================
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
]

def get_random_user_agent() -> str:
    """Rotate user agents to avoid fingerprinting."""
    return random.choice(USER_AGENTS)


# ======================================================
# HUMAN BEHAVIOR UTILITIES (from V03)
# ======================================================
async def human_pause(min_sec: float = 0.3, max_sec: float = 0.8):
    """
    Simulate human-like pause between actions.
    Shorter pauses for headless mode, still adds randomness.
    """
    await asyncio.sleep(random.uniform(min_sec, max_sec))


async def human_scroll(page, intensity: str = "light"):
    """
    Simulate human scrolling behavior.
    
    Args:
        page: Playwright page object
        intensity: "light" or "heavy"
    """
    try:
        if intensity == "light":
            delta = random.randint(200, 400)
        else:
            delta = random.randint(400, 800)
        
        await page.mouse.wheel(0, delta)
    except Exception:
        pass


async def human_mouse_move(page, x: int = None, y: int = None):
    """
    Simulate human mouse movement to random position.
    """
    try:
        if x is None:
            x = random.randint(100, 800)
        if y is None:
            y = random.randint(100, 500)
        
        await page.mouse.move(x, y, steps=random.randint(5, 15))
    except Exception:
        pass


async def simulate_human_behavior(page, scroll: bool = True, pause: bool = True):
    """
    Combined human-like behavior sequence.
    Use this after page loads to appear more human.
    """
    if pause:
        await human_pause(0.5, 1.5)
    
    await human_mouse_move(page)
    
    if scroll:
        await human_scroll(page, "light")
    
    if pause:
        await human_pause(0.3, 0.7)


# ======================================================
# CONTEXT FACTORY (Enhanced from V03)
# ======================================================
async def create_stealth_context(browser, persistent: bool = False):
    """
    Create a browser context with stealth settings applied.
    
    Args:
        browser: Playwright browser object
        persistent: Whether to use persistent profile
        
    Returns:
        Browser context with stealth settings
    """
    context = await browser.new_context(
        user_agent=get_random_user_agent(),
        viewport={"width": 1920, "height": 1080},
        locale="vi-VN",
        timezone_id="Asia/Ho_Chi_Minh",
        ignore_https_errors=True,
        java_script_enabled=True,
    )
    
    # Inject stealth script
    await context.add_init_script(STEALTH_INIT_SCRIPT)
    
    return context


# ======================================================
# RESOURCE BLOCKING
# ======================================================
async def block_heavy_resources(route):
    """
    Block heavy resources to speed up loading.
    Use with: await page.route("**/*", block_heavy_resources)
    """
    blocked_types = ["image", "font", "media", "other"]
    
    if route.request.resource_type in blocked_types:
        await route.abort()
    else:
        await route.continue_()


async def block_all_except_document(route):
    """
    Block everything except document and script.
    More aggressive - use with caution.
    """
    allowed_types = ["document", "script", "xhr", "fetch"]
    
    if route.request.resource_type in allowed_types:
        await route.continue_()
    else:
        await route.abort()
