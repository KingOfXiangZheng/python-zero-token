"""GLM（智谱）浏览器认证"""

import asyncio
from typing import Optional
from playwright.async_api import async_playwright, Browser, Page
from zero_token.models import AuthCredentials
from utils.storage import auth_storage


class GlmAuth:
    """GLM Web 认证"""

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
                    return None

            print("正在检查 GLM 登录状态...")

            target_url = "https://chatglm.cn"

            try:
                await self.page.goto(target_url)
            except Exception:
                pass

            await asyncio.sleep(2)

            current_url = self.page.url

            if "login" not in current_url:
                print("✓ 检测到已登录状态")
                print("正在捕获凭证...")
            else:
                print("\n❌ 未检测到登录状态")
                print("请在浏览器中登录 GLM (https://chatglm.cn)，然后重新运行此命令")
                return None

            self.credentials = await self._capture_credentials()

            if self.credentials:
                auth_storage.save_credentials("glm", self.credentials)

            return self.credentials

    async def _capture_credentials(self) -> AuthCredentials:
        cookies = await self.page.context.cookies(["https://chatglm.cn"])

        chatglm_refresh_token = None
        chatglm_token = None

        for cookie in cookies:
            if cookie["name"] == "chatglm_refresh_token":
                chatglm_refresh_token = cookie["value"]
            elif cookie["name"] == "chatglm_token":
                chatglm_token = cookie["value"]

        if not chatglm_refresh_token and not chatglm_token:
            print("❌ 未找到 GLM 认证 Cookie")
            print("请确保已在浏览器中登录 GLM")
            return None

        cookie_str = "; ".join([f"{c['name']}={c['value']}" for c in cookies])

        user_agent = await self.page.evaluate("() => navigator.userAgent")

        print(f"✓ 捕获到 Cookies ({len(cookies)} 个)")
        if chatglm_refresh_token:
            print(f"✓ chatglm_refresh_token: {chatglm_refresh_token[:30]}...")
        if chatglm_token:
            print(f"✓ chatglm_token: {chatglm_token[:30]}...")

        return AuthCredentials(
            cookie=cookie_str, bearer=chatglm_token, user_agent=user_agent
        )


async def main():
    auth = GlmAuth()
    credentials = await auth.login()
    if credentials:
        print(f"\n认证成功！")
        print(f"Cookie 长度: {len(credentials.cookie)}")


if __name__ == "__main__":
    asyncio.run(main())
