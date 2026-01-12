import asyncio
import os
import json
import traceback
from mcp_agent.app import MCPApp
from mcp_agent.agents.agent import Agent
from mcp_agent.workflows.llm.augmented_llm_openai import OpenAIAugmentedLLM, OpenAICompletionTasks, RequestCompletionRequest, _execute_openai_request
from mcp_agent.workflows.llm.augmented_llm import RequestParams
from mcp_agent.utils.common import ensure_serializable
from openai import AsyncAzureOpenAI
from playwright.async_api import async_playwright
from dotenv import load_dotenv
from app.core.token_tracker import TokenTracker

load_dotenv()

# --- Monkey Patch for Azure OpenAI (Global) ---
async def patched_request_completion_task(request: RequestCompletionRequest):
    api_key = os.getenv("AZURE_OPENAI_API_KEY") or request.config.api_key
    base_url = os.getenv("AZURE_OPENAI_ENDPOINT") or request.config.base_url
    api_version = os.getenv("AZURE_OPENAI_API_VERSION") or "2024-06-01"
    
    if os.getenv("AZURE_OPENAI_API_KEY") or "azure" in (base_url or ""):
        async with AsyncAzureOpenAI(
            api_key=api_key,
            api_version=api_version,
            azure_endpoint=base_url,
        ) as client:
            payload = request.payload
            if os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME"):
                payload["model"] = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME")

            response = await _execute_openai_request(client, payload)
            
            # TRACKING LOGIC
            try:
                if hasattr(response, 'usage') and response.usage:
                    TokenTracker.log_usage(
                        context="Agent Search (Azure)",
                        model=response.model or payload.get("model", "unknown"),
                        prompt_tokens=response.usage.prompt_tokens,
                        completion_tokens=response.usage.completion_tokens,
                        total_tokens=response.usage.total_tokens
                    )
            except Exception as e:
                print(f"Token Log Error: {e}")

            return ensure_serializable(response)
    else:
        from openai import AsyncOpenAI
        async with AsyncOpenAI(
            api_key=request.config.api_key,
            base_url=request.config.base_url,
        ) as client:
            return ensure_serializable(await _execute_openai_request(client, request.payload))

# Apply patch
OpenAICompletionTasks.request_completion_task = patched_request_completion_task

class BrowserAgentRunner:
    """
    Encapsulates a single run of the Browser Agent.
    Created per-request to ensure thread safety and clean state.
    """
    def __init__(self):
        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None
        self.mcp_app = None
        self.mcp_context = None
    
    async def cleanup(self):
        if self.page: await self.page.close()
        if self.context: await self.context.close()
        if self.browser: await self.browser.close()
        if self.playwright: await self.playwright.stop()
        if self.mcp_context: await self.mcp_context.__aexit__(None, None, None)

    # --- Tool Implementations (Bound to instance) ---
    async def navigate_to_url(self, url: str) -> str:
        try:
            print(f"[Browser] Navigating to: {url}")
            await self.page.goto(url, timeout=60000, wait_until='domcontentloaded')
            title = await self.page.title()
            content = await self.page.inner_text("body")
            summary = content[:2000] + "..." if len(content) > 2000 else content
            links_count = await self.page.locator("a").count()
            
            interactive_elements = await self.page.evaluate("""() => {
                const els = Array.from(document.querySelectorAll('input, button, textarea, select, [role="button"], [role="search"]'));
                return els.map(el => {
                    const rect = el.getBoundingClientRect();
                    const isVisible = rect.width > 0 && rect.height > 0 && window.getComputedStyle(el).visibility !== 'hidden';
                    if (!isVisible) return null;
                    
                    let label = el.getAttribute('aria-label') || el.getAttribute('placeholder') || el.innerText || el.value || el.name || el.id || '';
                    return {
                        tag: el.tagName.toLowerCase(),
                        type: el.type || '',
                        id: el.id ? '#' + el.id : '',
                        class: el.className ? '.' + el.className.split(' ').join('.') : '',
                        placeholder: el.placeholder || '',
                        label: label.trim().substring(0, 50)
                    };
                }).filter(el => el !== null);
            }""")
            
            elements_str = "\n".join([f"- <{el['tag']} {el['type']} {el['id']} {el['class']}> : '{el['label']}'" for el in interactive_elements[:20]])
            if len(interactive_elements) > 20:
                elements_str += f"\n... và {len(interactive_elements) - 20} phần tử khác"

            return f"✅ Đã mở: {url}\n📄 Tiêu đề: {title}\n🔗 Số links: {links_count}\n\n🎮 Các phần tử tương tác (Inputs/Buttons):\n{elements_str}\n\n📝 Nội dung (tóm tắt):\n{summary}"
        except Exception as e:
            return f"❌ Lỗi: {str(e)}"

    async def click_element(self, selector: str, wait_timeout: int = 10000) -> str:
        try:
            print(f"[Browser] Clicking: {selector}")
            try:
                await self.page.wait_for_selector(selector, state='visible', timeout=3000)
                await self.page.click(selector, timeout=wait_timeout)
                return f"✅ Đã click (selector): {selector}"
            except: pass

            try:
                element = self.page.get_by_text(selector, exact=True).first
                if await element.is_visible():
                    await element.click(timeout=wait_timeout)
                    return f"✅ Đã click (text exact): {selector}"
            except: pass
            
            try:
                element = self.page.get_by_text(selector).first
                if await element.is_visible():
                    await element.click(timeout=wait_timeout)
                    return f"✅ Đã click (text contains): {selector}"
            except: pass

            try:
                js_success = await self.page.evaluate(f"""(sel) => {{
                    const el = document.querySelector(sel);
                    if(el) {{ el.click(); return true; }}
                    const textEls = Array.from(document.querySelectorAll('*'))
                        .filter(el => el.textContent.includes(sel) && el.offsetParent !== null);
                    if(textEls.length > 0) {{ textEls[0].click(); return true; }}
                    return false;
                }}""", selector)
                if js_success: return f"✅ Đã click (JS Force): {selector}"
            except: pass
            return f"❌ Không thể click: {selector}"
        except Exception as e: return f"❌ Lỗi ngoại lệ: {str(e)}"

    async def type_text(self, selector: str, text: str, clear_first: bool = True) -> str:
        try:
            print(f"[Browser] Typing '{text}' into {selector}")
            if clear_first: await self.page.fill(selector, text, timeout=5000)
            else: await self.page.type(selector, text, timeout=5000)
            await self.page.keyboard.press("Enter")
            return f"✅ Đã nhập '{text}' vào {selector}"
        except Exception as e: return f"❌ Lỗi nhập text: {str(e)}"

    async def run(self, drug_name: str):
        try:
            # 1. Initialize Infrastructure
            self.mcp_app = MCPApp(name=f"agent_runner_{os.urandom(4).hex()}")
            self.mcp_context = self.mcp_app.run()
            await self.mcp_context.__aenter__()

            self.playwright = await async_playwright().start()
            self.browser = await self.playwright.chromium.launch(headless=True) # HEADLESS TRUE FOR SERVER
            self.context = await self.browser.new_context(
                 user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )
            self.page = await self.context.new_page()

            # 2. Define Agent (Using bound methods)
            # Note: mcp_agent expects functions. We pass bound methods, which work as callables.
            browser_agent = Agent(
                name="browser",
                functions=[
                    self.navigate_to_url, 
                    self.click_element, 
                    self.type_text
                    # Can add scroll/get_text if necessary, keeping minimal for speed
                ],
                instruction="""Bạn là một trợ lý nghiên cứu và tìm kiếm thông tin web NHANH NHẠY và THÔNG MINH.

CHIẾN LƯỢC TỐI ƯU (THEO TƯ DUY NGƯỜI DÙNG):
1. **Ưu tiên TÌM KIẾM (SEARCH) ngay lập tức**:
   - Vừa vào trang web -> Đảo mắt tìm ngay ô "Tìm kiếm" / "Search".
   - Đây là con đường ngắn nhất để đến thông tin. Đừng lãng phí thời gian đọc menu nếu có ô search.

2. **KẾT QUẢ MONG ĐỢI**:
   - Trả về JSON với format chính xác:
   {
      "input_name": "...",
      "official_name": "Tên chính thức tìm thấy",
      "sdk": "Số đăng ký",
      "active_ingredient": "Hoạt chất chính",
      "usage": "Công dụng/Chỉ định",
      "contraindications": "Chống chỉ định",
      "dosage": "Liều dùng",
      "source": "Web",
      "confidence": 0.9,
      "source_urls": ["url1", "url2"],
      "is_duplicate": false
   }
   - Nếu KHÔNG tìm thấy sau khi đã nỗ lực hết sức: Trả về JSON với các trường null và confidence thấp.
"""
            )
            await browser_agent.initialize()
            llm = await browser_agent.attach_llm(OpenAIAugmentedLLM)

            # 3. Execute Query
            search_query = f'''Hãy tìm kiếm thông tin chi tiết về thuốc "{drug_name}". 
CHIẾN LƯỢC:
1. KHÔNG dùng Google Search.
2. Dùng tool `navigate_to_url` vào trực tiếp "https://thuocbietduoc.com.vn/" và dùng ô tìm kiếm (class/id thường là `input#search-input` hoặc `input[name="q"]`).
3. Hoặc vào "https://drugbank.vn/".

Cần tìm: Số đăng ký, Hoạt chất, Công dụng, Chống chỉ định, Liều dùng.
Nếu tìm thấy, hãy click vào xem chi tiết để lấy thông tin.'''

            result = await llm.generate_str(
                message=search_query, 
                request_params=RequestParams(use_history=True, maxTokens=10000, max_iterations=20)
            )
            
            # 4. Parse Result
            try:
                json_str = result
                if "```json" in result:
                    json_str = result.split("```json")[1].split("```")[0].strip()
                elif "{" in result:
                    start = result.find("{")
                    end = result.rfind("}") + 1
                    json_str = result[start:end]
                return json.loads(json_str)
            except:
                return {"status": "error", "raw_result": result}

        except Exception as e:
            traceback.print_exc()
            return {"status": "error", "message": str(e)}
        finally:
            await self.cleanup()

async def run_agent_search(drug_name: str):
    runner = BrowserAgentRunner()
    return await runner.run(drug_name)
