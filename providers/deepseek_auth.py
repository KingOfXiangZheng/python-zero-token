"""DeepSeek 浏览器认证"""

import asyncio
from typing import Optional
from playwright.async_api import async_playwright, Browser, Page
from zero_token.models import AuthCredentials
from utils.storage import auth_storage


class DeepSeekAuth:
    """DeepSeek Web 认证"""

    def __init__(self):
        self.browser: Optional[Browser] = None
        self.page: Optional[Page] = None
        self.credentials: Optional[AuthCredentials] = None

    async def login(self, cdp_port: int = 9222) -> AuthCredentials:
        async with async_playwright() as p:
            print(f"正在连接到 Chrome (CDP: {cdp_port})...")

            cdp_url = f"http://127.0.0.1:{cdp_port}"

            import httpx

            async with httpx.AsyncClient() as client:
                try:
                    response = await client.get(f"{cdp_url}/json/version", timeout=2.0)

                    if response.status_code != 200:
                        raise Exception(f"Chrome CDP 返回错误: {response.status_code}")

                    data = response.json()
                    ws_url = data.get("webSocketDebuggerUrl")

                    if not ws_url:
                        raise Exception("未找到 WebSocket URL")

                    print(f"✓ 已连接到 Chrome")

                    self.browser = await p.chromium.connect_over_cdp(ws_url)
                    contexts = self.browser.contexts

                    if not contexts:
                        raise Exception("没有找到浏览器上下文")

                    context = contexts[0]
                    pages = context.pages

                    if not pages:
                        self.page = await context.new_page()
                    else:
                        self.page = pages[0]

                except Exception as e:
                    print(f"\n❌ 连接失败: {e}")
                    print("\n请确保 Chrome 已使用调试模式启动:")
                    print("  Windows:")
                    print(
                        "    chrome.exe --remote-debugging-port=9222 --user-data-dir=chrome-debug-profile"
                    )
                    print("  Mac:")
                    print(
                        "    /Applications/Google\\ Chrome.app/Contents/MacOS/Google\\ Chrome --remote-debugging-port=9222 --user-data-dir=chrome-debug-profile"
                    )
                    return None

            print("正在检查 DeepSeek 登录状态...")

            target_url = "https://chat.deepseek.com"

            try:
                await self.page.goto(target_url)
            except Exception:
                pass

            await asyncio.sleep(2)

            current_url = self.page.url

            if "login" not in current_url and "signin" not in current_url:
                print("✓ 检测到已登录状态")
                print("正在捕获凭证...")
            else:
                print("\n❌ 未检测到登录状态")
                print("请在浏览器中登录 DeepSeek，然后重新运行此命令")
                return None

            self.credentials = await self._capture_credentials()

            if self.credentials:
                auth_storage.save_credentials("deepseek", self.credentials)

            return self.credentials

    async def _capture_credentials(self) -> AuthCredentials:
        captured_bearer = None
        captured_cookies = None
        timeout = 30
        start_time = asyncio.get_event_loop().time()

        def on_request(request):
            nonlocal captured_bearer
            if "/api/v0/" in request.url:
                auth = request.headers.get("authorization", "")
                if auth.startswith("Bearer "):
                    captured_bearer = auth[7:]
                    print(f"✓ 捕获到 Bearer Token")

        async def on_response(response):
            nonlocal captured_bearer
            if "/api/v0/" in response.url and response.ok:
                try:
                    data = await response.json()
                    token = data.get("data", {}).get("biz_data", {}).get("token")
                    if token:
                        captured_bearer = token
                        print(f"✓ 从响应中捕获到 Token")
                except Exception:
                    pass

        self.page.on("request", on_request)
        self.page.on("response", lambda r: asyncio.create_task(on_response(r)))

        print("正在触发 API 请求...")

        try:
            await self.page.reload()
        except Exception:
            pass

        while True:
            elapsed = asyncio.get_event_loop().time() - start_time

            if elapsed > timeout:
                print(f"\n⚠️  超时 ({timeout}秒)")
                print("未捕获到 Bearer Token，但将继续使用 Cookies")
                break

            cookies = await self.page.context.cookies(["https://chat.deepseek.com"])
            cookie_str = "; ".join([f"{c['name']}={c['value']}" for c in cookies])

            if not captured_cookies and len(cookies) > 0:
                captured_cookies = cookie_str
                print(f"✓ 捕获到 Cookies ({len(cookies)} 个)")

            if captured_bearer:
                break

            await asyncio.sleep(1)

        cookies = await self.page.context.cookies(["https://chat.deepseek.com"])
        cookie_str = "; ".join([f"{c['name']}={c['value']}" for c in cookies])

        user_agent = await self.page.evaluate("() => navigator.userAgent")

        if not captured_bearer:
            print(
                "\n提示: 如果后续 API 调用失败，请尝试在浏览器中发起一次对话，然后重新运行此命令"
            )

        return AuthCredentials(
            cookie=cookie_str, bearer=captured_bearer, user_agent=user_agent
        )


async def main():
    auth = DeepSeekAuth()
    credentials = await auth.login()
    if credentials:
        print(f"\n认证成功！")
        print(f"Cookie 长度: {len(credentials.cookie)}")
        print(
            f"Bearer Token: {credentials.bearer[:20]}..."
            if credentials.bearer
            else "Bearer Token: 无"
        )


if __name__ == "__main__":
    asyncio.run(main())
