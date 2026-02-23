"""
AI 驱动的 UI 测试执行器
通过 Playwright 控制浏览器，结合 LLM 将自然语言测试步骤转换为浏览器操作
使用 CDP Screencast 实现实时浏览器画面推流
"""
import asyncio
import json
import logging
import os
import time
import uuid
from typing import AsyncGenerator, Callable, Optional

logger = logging.getLogger(__name__)

SCREENSHOT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "screenshots")
os.makedirs(SCREENSHOT_DIR, exist_ok=True)


async def _invoke_llm(prompt: str) -> str:
    from config.settings import llm
    loop = asyncio.get_event_loop()
    response = await loop.run_in_executor(None, lambda: llm.invoke(prompt))
    return response.content


def _extract_json(text: str) -> dict:
    text = text.strip()
    if text.startswith("```"):
        lines = text.split("\n")
        lines = [l for l in lines if not l.strip().startswith("```")]
        text = "\n".join(lines)
    start = text.find("{")
    end = text.rfind("}") + 1
    if start >= 0 and end > start:
        return json.loads(text[start:end])
    raise ValueError(f"Cannot extract JSON from LLM response: {text[:200]}")


class UiTestExecutor:
    """Playwright + AI + CDP Screencast 的 UI 测试执行器"""

    def __init__(self):
        self.playwright = None
        self.browser = None
        self.page = None
        self.cdp_session = None
        self._frame_callback = None
        self._screencast_active = False

    async def start(self, headless: bool = True):
        from playwright.async_api import async_playwright
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(headless=headless)
        self.page = await self.browser.new_page(viewport={"width": 1280, "height": 720})

    async def close(self):
        await self.stop_screencast()
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()

    # ======================== CDP Screencast ========================

    async def start_screencast(self, frame_callback: Callable):
        """
        启动 CDP Screencast，实时捕获浏览器画面帧。
        frame_callback(base64_jpeg: str) 会在每帧到达时被调用。
        """
        self._frame_callback = frame_callback
        self.cdp_session = await self.page.context.new_cdp_session(self.page)
        self._screencast_active = True

        def on_frame(params):
            if self._screencast_active and self._frame_callback:
                session_id = params.get("sessionId")
                frame_data = params.get("data", "")
                asyncio.ensure_future(self._handle_frame(session_id, frame_data))

        self.cdp_session.on("Page.screencastFrame", on_frame)

        await self.cdp_session.send("Page.startScreencast", {
            "format": "jpeg",
            "quality": 55,
            "maxWidth": 1280,
            "maxHeight": 720,
            "everyNthFrame": 2,
        })

    async def _handle_frame(self, session_id: str, frame_data: str):
        try:
            if self._frame_callback:
                await self._frame_callback(frame_data)
            if self.cdp_session and self._screencast_active:
                await self.cdp_session.send("Page.screencastFrameAck", {"sessionId": session_id})
        except Exception as e:
            logger.debug(f"Screencast frame handling error: {e}")

    async def stop_screencast(self):
        self._screencast_active = False
        self._frame_callback = None
        if self.cdp_session:
            try:
                await self.cdp_session.send("Page.stopScreencast")
                await self.cdp_session.detach()
            except Exception:
                pass
            self.cdp_session = None

    # ======================== 截图 ========================

    async def take_screenshot(self) -> str:
        filename = f"{uuid.uuid4().hex}.png"
        filepath = os.path.join(SCREENSHOT_DIR, filename)
        await self.page.screenshot(path=filepath)
        return filename

    # ======================== 页面元素提取 ========================

    async def get_page_interactive_elements(self) -> list:
        elements = await self.page.evaluate("""() => {
            const selectors = 'a, button, input, select, textarea, [role="button"], [onclick], [type="submit"], label';
            const els = document.querySelectorAll(selectors);
            return Array.from(els).slice(0, 80).map((el, i) => {
                const rect = el.getBoundingClientRect();
                if (rect.width === 0 && rect.height === 0) return null;
                return {
                    index: i,
                    tag: el.tagName.toLowerCase(),
                    type: el.type || '',
                    text: (el.innerText || el.value || el.placeholder || el.getAttribute('aria-label') || '').substring(0, 80).trim(),
                    id: el.id || '',
                    name: el.name || '',
                    className: (el.className || '').toString().substring(0, 80),
                    href: el.href || '',
                };
            }).filter(Boolean);
        }""")
        return elements

    # ======================== AI 规划与执行 ========================

    async def ai_plan_action(self, step_action: str, step_input: Optional[str], elements: list) -> dict:
        elements_text = json.dumps(elements[:50], ensure_ascii=False, indent=1)
        prompt = f"""你是一个UI自动化测试执行器。请根据测试步骤描述，从页面元素中选择正确的目标并生成操作指令。

当前页面URL: {self.page.url}
页面标题: {await self.page.title()}

页面可交互元素（最多50个）:
{elements_text}

测试步骤操作: {step_action}
{f'输入数据: {step_input}' if step_input else ''}

请返回一个JSON操作指令，支持以下类型:
- 点击: {{"action": "click", "selector": "CSS选择器或text=文本"}}
- 输入: {{"action": "fill", "selector": "CSS选择器", "value": "要输入的值"}}
- 导航: {{"action": "goto", "url": "完整URL"}}
- 选择下拉: {{"action": "select", "selector": "CSS选择器", "value": "选项值"}}
- 等待: {{"action": "wait", "seconds": 秒数}}
- 滚动: {{"action": "scroll", "direction": "down或up", "pixels": 500}}
- 键盘: {{"action": "press", "key": "Enter/Tab/Escape等"}}
- 悬浮: {{"action": "hover", "selector": "CSS选择器"}}

选择器优先使用 id > name > text= > CSS class。text= 选择器格式: text=按钮文字。
只返回一个JSON对象，不要其他内容。"""

        content = await _invoke_llm(prompt)
        return _extract_json(content)

    async def execute_action(self, action_data: dict) -> str:
        action = action_data.get("action", "")
        selector = action_data.get("selector", "")
        value = action_data.get("value", "")

        try:
            if action == "click":
                await self.page.click(selector, timeout=8000)
                return f"点击元素: {selector}"
            elif action == "fill":
                await self.page.fill(selector, value, timeout=8000)
                return f"输入 '{value}' 到: {selector}"
            elif action == "goto":
                url = action_data.get("url", "")
                await self.page.goto(url, wait_until="domcontentloaded", timeout=15000)
                return f"导航到: {url}"
            elif action == "select":
                await self.page.select_option(selector, value, timeout=8000)
                return f"选择 '{value}' 在: {selector}"
            elif action == "wait":
                seconds = int(action_data.get("seconds", 2))
                await self.page.wait_for_timeout(min(seconds, 10) * 1000)
                return f"等待 {seconds} 秒"
            elif action == "scroll":
                direction = action_data.get("direction", "down")
                pixels = int(action_data.get("pixels", 500))
                delta = pixels if direction == "down" else -pixels
                await self.page.evaluate(f"window.scrollBy(0, {delta})")
                return f"滚动{'下' if direction == 'down' else '上'} {pixels}px"
            elif action == "press":
                key = action_data.get("key", "Enter")
                await self.page.keyboard.press(key)
                return f"按键: {key}"
            elif action == "hover":
                await self.page.hover(selector, timeout=8000)
                return f"悬浮在: {selector}"
            else:
                return f"未知操作: {action}"
        except Exception as e:
            raise RuntimeError(f"执行操作失败 [{action}]: {str(e)}")

    async def ai_validate_result(self, expected_result: str) -> dict:
        page_text = ""
        try:
            page_text = await self.page.inner_text("body")
            page_text = page_text[:3000]
        except Exception:
            page_text = "(无法获取页面文本)"

        prompt = f"""你是一个UI测试验证器，判断当前页面状态是否符合预期结果。

当前页面URL: {self.page.url}
页面标题: {await self.page.title()}
页面文本内容（截取前3000字）:
{page_text}

预期结果: {expected_result}

请判断预期结果是否满足，返回JSON:
{{"passed": true或false, "reason": "简短判断理由"}}
只返回JSON。"""

        content = await _invoke_llm(prompt)
        return _extract_json(content)

    # ======================== 执行用例（供 WebSocket 使用） ========================

    async def run_case_live(self, page_url: str, steps: list, message_callback: Callable) -> dict:
        """
        执行完整用例，通过 message_callback 推送事件。
        Screencast 帧由 start_screencast 的 frame_callback 单独处理。
        返回: {"passed": int, "failed": int, "status": str}
        """
        try:
            await self.page.goto(page_url, wait_until="domcontentloaded", timeout=20000)
            await self.page.wait_for_timeout(1500)
        except Exception as e:
            await message_callback({"type": "error", "message": f"无法打开页面 {page_url}: {str(e)}"})
            return {"passed": 0, "failed": len(steps), "status": "error"}

        await message_callback({"type": "page_loaded", "url": self.page.url, "title": await self.page.title()})

        passed_count = 0
        failed_count = 0

        for step in steps:
            step_id = step["id"]
            step_start = time.time()

            await message_callback({"type": "step_start", "step_id": step_id, "sort_order": step["sort_order"], "action": step["action"]})

            try:
                elements = await self.get_page_interactive_elements()
                action_data = await self.ai_plan_action(step["action"], step.get("input_data"), elements)

                await message_callback({"type": "ai_thinking", "step_id": step_id, "action": json.dumps(action_data, ensure_ascii=False)})

                action_desc = await self.execute_action(action_data)
                await self.page.wait_for_timeout(1000)

                screenshot = await self.take_screenshot()

                validation = None
                step_passed = True
                if step.get("expected_result"):
                    validation = await self.ai_validate_result(step["expected_result"])
                    step_passed = validation.get("passed", False)

                duration_ms = int((time.time() - step_start) * 1000)

                if step_passed:
                    passed_count += 1
                else:
                    failed_count += 1

                await message_callback({
                    "type": "step_done",
                    "step_id": step_id,
                    "status": "passed" if step_passed else "failed",
                    "screenshot": screenshot,
                    "ai_action": json.dumps(action_data, ensure_ascii=False),
                    "actual_result": action_desc + (f" | 验证: {validation.get('reason', '')}" if validation else ""),
                    "duration_ms": duration_ms,
                })

            except Exception as e:
                failed_count += 1
                screenshot = None
                try:
                    screenshot = await self.take_screenshot()
                except Exception:
                    pass
                duration_ms = int((time.time() - step_start) * 1000)

                await message_callback({
                    "type": "step_done",
                    "step_id": step_id,
                    "status": "failed",
                    "screenshot": screenshot,
                    "ai_action": None,
                    "actual_result": None,
                    "error_message": str(e),
                    "duration_ms": duration_ms,
                })

        final_status = "passed" if failed_count == 0 else "failed"
        await message_callback({"type": "done", "status": final_status, "passed": passed_count, "failed": failed_count})
        return {"passed": passed_count, "failed": failed_count, "status": final_status}
