"""豆包（Doubao）浏览器认证"""

import asyncio
import json
from typing import Optional
from playwright.async_api import async_playwright, Browser
from zero_token.models import AuthCredentials
from utils.storage import auth_storage


class DoubaoAuth:
    """豆包 Web 认证"""
    
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
                    resp = await client.get(f"http://127.0.0.1:{cdp_port}/json/version", timeout=2.0)
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
            
            print("正在检查豆包登录状态...")
            await self.page.goto("https://www.doubao.com/", wait_until="domcontentloaded")
            await asyncio.sleep(3)
            
            current_url = self.page.url
            if "login" in current_url.lower():
                print("\n❌ 未检测到登录状态")
                print("请先在浏览器中登录豆包 (https://www.doubao.com)")
                return None
            
            print("✓ 检测到已登录状态")
            print("正在捕获凭证...")
            
            self.credentials = await self._capture_credentials()
            
            if self.credentials:
                auth_storage.save_credentials("doubao", self.credentials)
            
            return self.credentials
    
    async def _capture_credentials(self) -> Optional[AuthCredentials]:
        """捕获所有豆包相关的 cookies"""
        all_cookies = await self.page.context.cookies()
        
        print(f"总共捕获 {len(all_cookies)} 个 cookies")
        
        doubao_cookies = []
        auth_token = None
        session_id = None
        
        for cookie in all_cookies:
            name = cookie.get("name", "")
            value = cookie.get("value", "")
            
            if value:
                doubao_cookies.append(f"{name}={value}")
            
            # 查找认证相关 cookie
            if "auth" in name.lower() or "token" in name.lower() or "session" in name.lower():
                print(f"  找到：{name}={value[:30]}..." if len(value) > 30 else f"  找到：{name}={value}")
                
                if "auth" in name.lower():
                    auth_token = value
                if "session" in name.lower():
                    session_id = value
        
        cookie_str = "; ".join(doubao_cookies)
        user_agent = await self.page.evaluate("() => navigator.userAgent")
        
        credentials = AuthCredentials(
            cookie=cookie_str,
            bearer=auth_token or session_id,
            user_agent=user_agent
        )
        
        print(f"✓ Cookie 长度：{len(cookie_str)}")
        if credentials.bearer:
            print(f"✓ Bearer: {credentials.bearer[:30]}...")
        
        return credentials


async def main():
    auth = DoubaoAuth()
    credentials = await auth.login()
    if credentials:
        print(f"\n认证成功！")
        print(f"Cookie 长度：{len(credentials.cookie)}")

if __name__ == '__main__':
    asyncio.run(main())
