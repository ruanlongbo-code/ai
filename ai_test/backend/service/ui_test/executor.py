"""
AI 驱动的 UI 测试执行器
通过 Playwright 控制浏览器，结合多模态 LLM（视觉模型）将自然语言测试步骤转换为浏览器操作
使用 CDP Screencast 实现实时浏览器画面推流
支持截图视觉分析：AI 根据页面截图 + DOM 元素列表进行操作决策和结果验证
支持结构化断言：url_contains/url_equals/title_contains/element_visible/element_text_contains 等
"""
import asyncio
import base64
import json
import logging
import os
import time
import uuid
from typing import AsyncGenerator, Callable, Optional

from langchain_core.messages import HumanMessage

logger = logging.getLogger(__name__)

SCREENSHOT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "screenshots")
os.makedirs(SCREENSHOT_DIR, exist_ok=True)

# 支持的断言类型
ASSERTION_TYPES = [
    "url_contains", "url_equals",
    "title_contains", "title_equals",
    "element_visible", "element_hidden",
    "element_text_contains", "element_text_equals",
    "element_exists",
    "page_contains",
    "toast_contains",
]


async def _invoke_llm(prompt: str) -> str:
    """调用文本 LLM"""
    from config.settings import llm
    loop = asyncio.get_event_loop()
    response = await loop.run_in_executor(None, lambda: llm.invoke(prompt))
    return response.content


async def _invoke_vision_llm(prompt: str, image_base64: str) -> str:
    """调用视觉 LLM（支持图片输入的多模态模型）"""
    from config.settings import vision_llm
    message = HumanMessage(
        content=[
            {"type": "text", "text": prompt},
            {
                "type": "image_url",
                "image_url": {"url": f"data:image/png;base64,{image_base64}"},
            },
        ]
    )
    loop = asyncio.get_event_loop()
    response = await loop.run_in_executor(None, lambda: vision_llm.invoke([message]))
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
    """Playwright + 多模态AI + CDP Screencast 的 UI 测试执行器"""

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

    async def take_screenshot_base64(self) -> str:
        screenshot_bytes = await self.page.screenshot()
        return base64.b64encode(screenshot_bytes).decode("utf-8")

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
                    rect: { x: Math.round(rect.x), y: Math.round(rect.y), w: Math.round(rect.width), h: Math.round(rect.height) },
                };
            }).filter(Boolean);
        }""")
        return elements

    # ======================== 结构化断言 ========================

    async def run_assertion(self, assertion_type: str, assertion_target: Optional[str],
                            assertion_value: Optional[str]) -> dict:
        """
        执行结构化断言，返回断言结果。
        返回: {"passed": bool, "detail": str, "actual": str}
        """
        if not assertion_type:
            return {"passed": True, "detail": "无断言", "actual": ""}

        try:
            actual = ""

            if assertion_type == "url_contains":
                actual = self.page.url
                passed = assertion_value in actual if assertion_value else True
                detail = f"URL '{actual}' {'包含' if passed else '不包含'} '{assertion_value}'"

            elif assertion_type == "url_equals":
                actual = self.page.url
                passed = actual == assertion_value
                detail = f"URL 期望 '{assertion_value}'，实际 '{actual}'"

            elif assertion_type == "title_contains":
                actual = await self.page.title()
                passed = assertion_value in actual if assertion_value else True
                detail = f"标题 '{actual}' {'包含' if passed else '不包含'} '{assertion_value}'"

            elif assertion_type == "title_equals":
                actual = await self.page.title()
                passed = actual == assertion_value
                detail = f"标题 期望 '{assertion_value}'，实际 '{actual}'"

            elif assertion_type == "element_visible":
                try:
                    el = self.page.locator(assertion_target)
                    visible = await el.is_visible(timeout=5000)
                    actual = f"元素 '{assertion_target}' 可见={visible}"
                    passed = visible
                    detail = f"元素 '{assertion_target}' {'可见' if passed else '不可见'}"
                except Exception as e:
                    actual = str(e)
                    passed = False
                    detail = f"查找元素 '{assertion_target}' 失败: {str(e)}"

            elif assertion_type == "element_hidden":
                try:
                    el = self.page.locator(assertion_target)
                    visible = await el.is_visible(timeout=3000)
                    actual = f"元素 '{assertion_target}' 可见={visible}"
                    passed = not visible
                    detail = f"元素 '{assertion_target}' {'已隐藏' if passed else '仍可见'}"
                except Exception:
                    # 元素不存在也认为是隐藏的
                    passed = True
                    actual = "元素不存在"
                    detail = f"元素 '{assertion_target}' 不存在（视为隐藏）"

            elif assertion_type == "element_text_contains":
                try:
                    el = self.page.locator(assertion_target)
                    text = await el.inner_text(timeout=5000)
                    actual = text[:500]
                    passed = assertion_value in text if assertion_value else True
                    detail = f"元素文本 {'包含' if passed else '不包含'} '{assertion_value}'，实际文本: '{actual[:100]}'"
                except Exception as e:
                    actual = str(e)
                    passed = False
                    detail = f"获取元素文本失败: {str(e)}"

            elif assertion_type == "element_text_equals":
                try:
                    el = self.page.locator(assertion_target)
                    text = (await el.inner_text(timeout=5000)).strip()
                    actual = text[:500]
                    passed = text == assertion_value
                    detail = f"元素文本 期望 '{assertion_value}'，实际 '{actual[:100]}'"
                except Exception as e:
                    actual = str(e)
                    passed = False
                    detail = f"获取元素文本失败: {str(e)}"

            elif assertion_type == "element_exists":
                try:
                    el = self.page.locator(assertion_target)
                    count = await el.count()
                    actual = f"找到 {count} 个元素"
                    passed = count > 0
                    detail = f"元素 '{assertion_target}' {'存在' if passed else '不存在'}，找到 {count} 个"
                except Exception as e:
                    actual = str(e)
                    passed = False
                    detail = f"查找元素失败: {str(e)}"

            elif assertion_type == "page_contains":
                try:
                    body_text = await self.page.inner_text("body")
                    actual = f"页面文本长度: {len(body_text)}"
                    passed = assertion_value in body_text if assertion_value else True
                    detail = f"页面 {'包含' if passed else '不包含'} 文本 '{assertion_value}'"
                except Exception as e:
                    actual = str(e)
                    passed = False
                    detail = f"获取页面文本失败: {str(e)}"

            elif assertion_type == "toast_contains":
                try:
                    # 常见的 toast/message 选择器
                    toast_selectors = [
                        ".el-message",  # Element Plus
                        ".el-notification",
                        ".ant-message",  # Ant Design
                        ".ant-notification",
                        ".toast",
                        ".message",
                        "[role='alert']",
                        ".v-snack",  # Vuetify
                    ]
                    toast_text = ""
                    for sel in toast_selectors:
                        try:
                            locator = self.page.locator(sel)
                            count = await locator.count()
                            if count > 0:
                                toast_text = await locator.first.inner_text(timeout=3000)
                                break
                        except Exception:
                            continue

                    actual = toast_text[:200] if toast_text else "未找到提示消息"
                    passed = assertion_value in toast_text if assertion_value and toast_text else False
                    detail = f"提示消息 {'包含' if passed else '不包含'} '{assertion_value}'，实际: '{actual}'"
                except Exception as e:
                    actual = str(e)
                    passed = False
                    detail = f"查找提示消息失败: {str(e)}"
            else:
                return {"passed": True, "detail": f"未知断言类型: {assertion_type}", "actual": ""}

            return {"passed": passed, "detail": detail, "actual": actual}

        except Exception as e:
            return {"passed": False, "detail": f"断言执行异常: {str(e)}", "actual": str(e)}

    # ======================== AI 视觉规划与执行 ========================

    async def ai_plan_action(self, step_action: str, step_input: Optional[str], elements: list) -> dict:
        screenshot_b64 = await self.take_screenshot_base64()
        elements_text = json.dumps(elements[:50], ensure_ascii=False, indent=1)

        prompt = f"""你是一个UI自动化测试执行器，具有视觉理解能力。请结合以下信息，根据测试步骤描述选择正确的目标并生成操作指令。

【重要】你可以看到页面截图，请结合截图中的视觉信息和DOM元素列表来做出决策。

当前页面URL: {self.page.url}
页面标题: {await self.page.title()}

页面可交互元素（最多50个，含坐标位置）:
{elements_text}

测试步骤操作: {step_action}
{f'输入数据: {step_input}' if step_input else ''}

请返回一个JSON操作指令，支持以下类型:
- 点击: {{"action": "click", "selector": "CSS选择器或text=文本", "description": "简要说明点击了什么"}}
- 输入: {{"action": "fill", "selector": "CSS选择器", "value": "要输入的值", "description": "说明"}}
- 导航: {{"action": "goto", "url": "完整URL", "description": "说明"}}
- 选择下拉: {{"action": "select", "selector": "CSS选择器", "value": "选项值", "description": "说明"}}
- 等待: {{"action": "wait", "seconds": 秒数, "description": "说明"}}
- 滚动: {{"action": "scroll", "direction": "down或up", "pixels": 500, "description": "说明"}}
- 键盘: {{"action": "press", "key": "Enter/Tab/Escape等", "description": "说明"}}
- 悬浮: {{"action": "hover", "selector": "CSS选择器", "description": "说明"}}

选择器优先使用 id > name > text= > CSS class。text= 选择器格式: text=按钮文字。
请在description字段中用中文简要说明你在截图中看到了什么以及为什么选择这个操作。
只返回一个JSON对象，不要其他内容。"""

        try:
            content = await _invoke_vision_llm(prompt, screenshot_b64)
        except Exception as e:
            logger.warning(f"Vision LLM failed, falling back to text LLM: {e}")
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
        screenshot_b64 = await self.take_screenshot_base64()

        page_text = ""
        try:
            page_text = await self.page.inner_text("body")
            page_text = page_text[:2000]
        except Exception:
            page_text = "(无法获取页面文本)"

        prompt = f"""你是一个UI测试验证器，具有视觉理解能力。请结合页面截图和页面信息，判断当前页面状态是否符合预期结果。

【重要】请仔细观察截图中的视觉内容（包括页面布局、弹窗提示、颜色变化、图标状态等），结合文本信息做出综合判断。

当前页面URL: {self.page.url}
页面标题: {await self.page.title()}
页面文本内容（截取前2000字）:
{page_text}

预期结果: {expected_result}

请判断预期结果是否满足，返回JSON:
{{"passed": true或false, "reason": "基于截图视觉分析和文本内容的判断理由（中文）", "visual_details": "从截图中观察到的关键视觉细节"}}
只返回JSON。"""

        try:
            content = await _invoke_vision_llm(prompt, screenshot_b64)
        except Exception as e:
            logger.warning(f"Vision LLM validation failed, falling back to text LLM: {e}")
            fallback_prompt = f"""你是一个UI测试验证器，判断当前页面状态是否符合预期结果。

当前页面URL: {self.page.url}
页面标题: {await self.page.title()}
页面文本内容（截取前2000字）:
{page_text}

预期结果: {expected_result}

请判断预期结果是否满足，返回JSON:
{{"passed": true或false, "reason": "简短判断理由"}}
只返回JSON。"""
            content = await _invoke_llm(fallback_prompt)

        return _extract_json(content)

    # ======================== 执行单步（含断言） ========================

    async def _execute_step(self, step: dict) -> dict:
        """
        执行单个步骤：AI规划 -> 执行操作 -> AI验证预期结果 -> 结构化断言
        返回步骤执行结果字典
        """
        step_id = step["id"]
        step_start = time.time()

        result = {
            "step_id": step_id,
            "sort_order": step.get("sort_order", 0),
            "action_data": None,
            "action_desc": None,
        }

        try:
            # 1. AI 规划动作
            elements = await self.get_page_interactive_elements()
            action_data = await self.ai_plan_action(step["action"], step.get("input_data"), elements)
            result["action_data"] = action_data

            # 2. 执行动作
            action_desc = await self.execute_action(action_data)
            result["action_desc"] = action_desc
            await self.page.wait_for_timeout(1000)

            # 3. 截图
            screenshot = await self.take_screenshot()
            result["screenshot"] = screenshot

            # 4. AI 验证预期结果
            validation = None
            ai_passed = True
            if step.get("expected_result"):
                validation = await self.ai_validate_result(step["expected_result"])
                ai_passed = validation.get("passed", False)

            # 5. 结构化断言
            assertion_result = None
            assertion_passed = True
            if step.get("assertion_type"):
                assertion_result = await self.run_assertion(
                    step["assertion_type"],
                    step.get("assertion_target"),
                    step.get("assertion_value"),
                )
                assertion_passed = assertion_result.get("passed", True)

            # 综合判断：AI验证和结构化断言都通过才算通过
            step_passed = ai_passed and assertion_passed
            duration_ms = int((time.time() - step_start) * 1000)

            actual_result = action_desc
            if validation:
                actual_result += f" | 验证: {validation.get('reason', '')}"
                visual = validation.get("visual_details")
                if visual:
                    actual_result += f" | 视觉分析: {visual}"
            if assertion_result and not assertion_passed:
                actual_result += f" | 断言失败: {assertion_result.get('detail', '')}"

            result.update({
                "status": "passed" if step_passed else "failed",
                "ai_action": json.dumps(action_data, ensure_ascii=False),
                "actual_result": actual_result,
                "duration_ms": duration_ms,
                "assertion_type": step.get("assertion_type"),
                "assertion_passed": assertion_passed if step.get("assertion_type") else None,
                "assertion_detail": assertion_result.get("detail") if assertion_result else None,
            })

        except Exception as e:
            screenshot = None
            try:
                screenshot = await self.take_screenshot()
            except Exception:
                pass
            duration_ms = int((time.time() - step_start) * 1000)

            result.update({
                "status": "failed",
                "screenshot": screenshot,
                "ai_action": None,
                "actual_result": None,
                "error_message": str(e),
                "duration_ms": duration_ms,
                "assertion_type": step.get("assertion_type"),
                "assertion_passed": False if step.get("assertion_type") else None,
                "assertion_detail": f"步骤执行异常，断言未能执行: {str(e)}" if step.get("assertion_type") else None,
            })

        return result

    # ======================== 执行用例 - 异步生成器（供 SSE 使用） ========================

    async def run_case(self, page_url: str, steps: list, preconditions: Optional[str] = None) -> AsyncGenerator[dict, None]:
        try:
            await self.page.goto(page_url, wait_until="domcontentloaded", timeout=20000)
            await self.page.wait_for_timeout(1500)
        except Exception as e:
            yield {"type": "error", "message": f"无法打开页面 {page_url}: {str(e)}"}
            return

        init_screenshot = await self.take_screenshot()
        yield {"type": "init", "screenshot": init_screenshot, "url": self.page.url, "title": await self.page.title()}

        passed_count = 0
        failed_count = 0

        for step in steps:
            yield {
                "type": "step_start",
                "step_id": step["id"],
                "sort_order": step["sort_order"],
                "action": step["action"],
            }

            result = await self._execute_step(step)

            if result.get("action_data"):
                yield {
                    "type": "ai_thinking",
                    "step_id": step["id"],
                    "action": json.dumps(result["action_data"], ensure_ascii=False),
                    "description": result["action_data"].get("description", ""),
                }

            if result["status"] == "passed":
                passed_count += 1
            else:
                failed_count += 1

            yield {
                "type": "step_done",
                "step_id": step["id"],
                "sort_order": step.get("sort_order", 0),
                "status": result["status"],
                "screenshot": result.get("screenshot"),
                "ai_action": result.get("ai_action"),
                "actual_result": result.get("actual_result"),
                "error_message": result.get("error_message"),
                "duration_ms": result.get("duration_ms"),
                "assertion_type": result.get("assertion_type"),
                "assertion_passed": result.get("assertion_passed"),
                "assertion_detail": result.get("assertion_detail"),
            }

        final_status = "passed" if failed_count == 0 else "failed"
        yield {"type": "done", "status": final_status, "passed": passed_count, "failed": failed_count}

    # ======================== 执行用例（供 WebSocket 使用） ========================

    async def run_case_live(self, page_url: str, steps: list, message_callback: Callable) -> dict:
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
            await message_callback({
                "type": "step_start",
                "step_id": step["id"],
                "sort_order": step["sort_order"],
                "action": step["action"],
            })

            result = await self._execute_step(step)

            if result.get("action_data"):
                await message_callback({
                    "type": "ai_thinking",
                    "step_id": step["id"],
                    "action": json.dumps(result["action_data"], ensure_ascii=False),
                    "description": result["action_data"].get("description", ""),
                })

            if result["status"] == "passed":
                passed_count += 1
            else:
                failed_count += 1

            await message_callback({
                "type": "step_done",
                "step_id": step["id"],
                "sort_order": step.get("sort_order", 0),
                "status": result["status"],
                "screenshot": result.get("screenshot"),
                "ai_action": result.get("ai_action"),
                "actual_result": result.get("actual_result"),
                "error_message": result.get("error_message"),
                "duration_ms": result.get("duration_ms"),
                "assertion_type": result.get("assertion_type"),
                "assertion_passed": result.get("assertion_passed"),
                "assertion_detail": result.get("assertion_detail"),
            })

        final_status = "passed" if failed_count == 0 else "failed"
        await message_callback({"type": "done", "status": final_status, "passed": passed_count, "failed": failed_count})
        return {"passed": passed_count, "failed": failed_count, "status": final_status}
