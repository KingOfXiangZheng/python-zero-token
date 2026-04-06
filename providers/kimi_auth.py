"""Kimi 浏览器认证 - 修复token提取"""

import asyncio
from typing import Optional, List
from playwright.async_api import async_playwright, Browser
from zero_token.models import AuthCredentials
from utils.storage import auth_storage


class KimiAuth:
    def __init__(self):
        self.browser: Optional[Browser] = None
        self.page = None
        self.credentials: Optional[AuthCredentials] = None

    async def login(self, cdp_port=9222):
        async with async_playwright() as p:
            print(f"连接到 Chrome (CDP: {cdp_port})...")

            import httpx

            async with httpx.AsyncClient() as client:
                try:
                    resp = await client.get(
                        f"http://127.0.0.1:{cdp_port}/json/version", timeout=2.0
                    )
                    if resp.status_code != 200:
                        raise Exception(f"Chrome CDP error: {resp.status_code}")

                    ws_url = resp.json().get("webSocketDebuggerUrl")
                    if not ws_url:
                        raise Exception("No WebSocket URL")

                    print(f"✓ 已连接到 Chrome")

                    self.browser = await p.chromium.connect_over_cdp(ws_url)
                    contexts = self.browser.contexts

                    if not contexts:
                        raise Exception("No browser context found")

                    context = contexts[0]
                    pages = context.pages

                    if pages:
                        self.page = pages[0]
                    else:
                        self.page = await context.new_page()

                except Exception as e:
                    print(f"\n❌ 连接失败：{e}")
                    return None

            print("正在检查 Kimi 登录状态...")

            target_url = "https://www.kimi.com/"

            try:
                await self.page.goto(target_url)
            except Exception:
                pass

            await asyncio.sleep(3)

            current_url = self.page.url
            if "login" in current_url.lower():
                print("\n❌ 未检测到登录状态")
                print("请在浏览器中登录 Kimi (https://www.kimi.com)")
                return None

            print("✓ 检测到已登录状态")
            print("正在捕获凭证...")

            self.credentials = await self._capture_credentials()

            if self.credentials:
                auth_storage.save_credentials("kimi", self.credentials)

            return self.credentials

    async def _capture_credentials(self) -> Optional[AuthCredentials]:
        all_cookies = await self.page.context.cookies()

        print(f"总共捕获 {len(all_cookies)} 个 cookies")

        kimi_cookies = []
        kimi_auth = None
        access_token = None

        for cookie in all_cookies:
            name = cookie.get("name", "")
            value = cookie.get("value", "")
            domain = cookie.get("domain", "")

            if value:
                kimi_cookies.append(f"{name}={value}")

            if name == "kimi-auth":
                print(f"  ✓ 找到 kimi-auth cookie")
                kimi_auth = value

            if name == "access_token":
                print(f"  ✓ 找到 access_token cookie")
                access_token = value

        if not kimi_auth and not access_token:
            print("  ⚠️ 尝试从localStorage获取token...")

            token_result = await self.page.evaluate("""
            () => {
                // 检查localStorage
                for (const key in localStorage) {
                    if (key.includes('token') || key.includes('auth')) {
                        const value = localStorage.getItem(key);
                        console.log("[Kimi] localStorage key:", key);
                        if (value) {
                            return { source: 'localStorage', key: key, value: value };
                        }
                    }
                }
                
                // 检查sessionStorage
                for (const key in sessionStorage) {
                    if (key.includes('token') || key.includes('auth')) {
                        const value = sessionStorage.getItem(key);
                        console.log("[Kimi] sessionStorage key:", key);
                        if (value) {
                            return { source: 'sessionStorage', key: key, value: value };
                        }
                    }
                }
                
                return null;
            }
            """)

            if token_result:
                print(f"  ✓ 从{token_result['source']}找到token: {token_result['key']}")
                access_token = token_result["value"]

        cookie_str = "; ".join(kimi_cookies)
        user_agent = await self.page.evaluate("() => navigator.userAgent")

        bearer = access_token or kimi_auth

        if not bearer:
            print("\n❌ 无法找到认证token (kimi-auth 或 access_token)")
            print("   请确保已登录 Kimi 并刷新页面")
            return None

        credentials = AuthCredentials(
            cookie=cookie_str, bearer=bearer, user_agent=user_agent
        )

        print(f"✓ Cookie 长度：{len(cookie_str)}")
        print(f"✓ Bearer token：{bearer[:30]}...")

        return credentials


async def main():
    auth = KimiAuth()
    credentials = await auth.login()
    if credentials:
        print(f"\n认证成功！")
        print(f"Cookie 长度：{len(credentials.cookie)}")


if __name__ == "__main__":
    asyncio.run(main())
