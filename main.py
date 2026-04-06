"""Main entry point"""

import asyncio
import sys
from zero_token.config import settings
from zero_token.server import start_server
from providers.deepseek_auth import DeepSeekAuth
from providers.glm_auth import GlmAuth
from providers.kimi_auth import KimiAuth
from providers.doubao_auth import DoubaoAuth
from utils.storage import auth_storage
from utils.browser_launcher import ensure_chrome_running
from playwright.async_api import async_playwright


def print_banner():
    print("""
========================================
  Zero Token API Server
  Free LLM API via browser automation
========================================
    """)


def cmd_serve():
    print_banner()
    print(f"Server running on http://{settings.host}:{settings.port}")
    print(f"Docs: http://{settings.host}:{settings.port}/docs")
    print("\nRun 'python main.py auth' first if no credentials\n")
    start_server()


def cmd_auth():
    print_banner()
    print("Starting authentication...\n")

    print(f"Checking Chrome status...")
    chrome_running = ensure_chrome_running(
        cdp_port=settings.chrome_cdp_port,
        user_data_dir=settings.chrome_user_data_dir,
        auto_start=settings.auto_start_chrome,
    )

    if not chrome_running:
        print("\n❌ Chrome is not running. Please start Chrome manually:")
        print(
            f"  chrome.exe --remote-debugging-port={settings.chrome_cdp_port} --user-data-dir={settings.chrome_user_data_dir}"
        )
        return

    print()

    providers = auth_storage.list_providers()
    if providers:
        print("Existing providers:")
        for p in providers:
            print(f"  - {p}")
        print()

    login_urls = {
        "deepseek": "https://chat.deepseek.com",
        "glm": "https://chatglm.cn",
        "kimi": "https://www.kimi.com",
        "doubao": "https://www.doubao.com",
    }

    provider_names = {
        "deepseek": "DeepSeek",
        "glm": "GLM (智谱)",
        "kimi": "Kimi (月之暗面)",
        "doubao": "豆包 (Doubao)",
    }

    existing_providers = set()
    missing_providers = [p for p in login_urls.keys() if p not in existing_providers]

    if existing_providers:
        print("✓ Already authenticated:")
        for p in existing_providers:
            print(f"  - {provider_names[p]}")

    if missing_providers:
        print("\n需要登录的平台:")
        for p in missing_providers:
            print(f"  - {provider_names[p]}")
        print("\n🚀 正在打开登录页面...")
        print("请在浏览器中完成登录，然后按 Enter 键继续...\n")

        for provider in missing_providers:
            print(f"  Opening {provider_names[provider]}: {login_urls[provider]}")

        async def open_login_pages():
            async with async_playwright() as p:
                import httpx

                async with httpx.AsyncClient() as client:
                    response = await client.get(
                        f"http://127.0.0.1:{settings.chrome_cdp_port}/json/version",
                        timeout=2.0,
                    )
                    data = response.json()
                    ws_url = data.get("webSocketDebuggerUrl")
                    browser = await p.chromium.connect_over_cdp(ws_url)
                    contexts = browser.contexts

                    if not contexts:
                        print("❌ No browser context found")
                        return None

                    context = contexts[0]
                    pages = context.pages

                    opened_count = 0
                    skipped_count = 0

                    for provider in missing_providers:
                        target_url = login_urls[provider]

                        page_exists = False
                        for page in pages:
                            if page.url.startswith(target_url) or target_url.startswith(
                                page.url
                            ):
                                print(
                                    f"  ✓ {provider_names[provider]} 页面已打开，跳过"
                                )
                                page_exists = True
                                skipped_count += 1
                                break

                        if not page_exists:
                            try:
                                page = await context.new_page()
                                await page.goto(
                                    target_url, wait_until="domcontentloaded"
                                )
                                await asyncio.sleep(0.5)
                                opened_count += 1
                                pages = context.pages
                            except Exception as e:
                                print(f"  ⚠️  Failed to open {provider}: {e}")

                    if opened_count > 0:
                        print(f"\n✓ 已打开 {opened_count} 个登录页面")
                    if skipped_count > 0:
                        print(f"  跳过 {skipped_count} 个已打开的页面")
                    return browser

        browser = asyncio.run(open_login_pages())

        print("\n" + "=" * 50)
        print("请在浏览器中完成所有平台的登录")
        print("登录完成后，按 Enter 键继续捕获凭证...")
        print("=" * 50 + "\n")
        input()

        print("🔄 开始捕获凭证...\n")

        success_count = 0
        failed_count = 0

        for provider in missing_providers:
            print(f"\n正在捕获 {provider_names[provider]} 凭证...")

            credentials = None
            try:
                if provider == "deepseek":
                    auth = DeepSeekAuth()
                    credentials = asyncio.run(
                        auth.login(cdp_port=settings.chrome_cdp_port)
                    )
                elif provider == "glm":
                    auth = GlmAuth()
                    credentials = asyncio.run(
                        auth.login(cdp_port=settings.chrome_cdp_port)
                    )
                elif provider == "kimi":
                    auth = KimiAuth()
                    credentials = asyncio.run(
                        auth.login(cdp_port=settings.chrome_cdp_port)
                    )
                elif provider == "doubao":
                    auth = DoubaoAuth()
                    credentials = asyncio.run(
                        auth.login(cdp_port=settings.chrome_cdp_port)
                    )

                if credentials:
                    print(f"  ✅ 认证成功!")
                    print(f"     Cookie 长度: {len(credentials.cookie)}")
                    if credentials.bearer:
                        print(f"     Bearer: {credentials.bearer[:30]}...")
                    success_count += 1
                else:
                    print(f"  ❌ 认证失败")
                    failed_count += 1
            except Exception as e:
                print(f"  ❌ 认证失败: {e}")
                failed_count += 1

        print("\n" + "=" * 50)
        print(f"凭证捕获完成!")
        print(f"  ✅ 成功: {success_count} 个平台")
        print(f"  ❌ 失败: {failed_count} 个平台")
        print(f"  凭证文件: {settings.auth_file}")
        print("=" * 50)
        print("\n现在可以运行 'python main.py serve' 启动服务\n")

        if browser:

            async def close_browser():
                await browser.close()

            asyncio.run(close_browser())
    else:
        print("\n所有平台都已认证完成！")
        print("如需重新认证，可以删除凭证文件或运行认证流程。")
        return


def cmd_list():
    print_banner()
    print("Authenticated providers:\n")

    providers = auth_storage.list_providers()

    if not providers:
        print("  No credentials found")
        print("\nRun 'python main.py auth' to add credentials\n")
    else:
        for provider in providers:
            credentials = auth_storage.get_credentials(provider)
            print(f"  ✓ {provider}")
            if credentials:
                print(f"    - Created: {credentials.created_at}")
                if credentials.bearer:
                    print(f"    - Bearer: {credentials.bearer[:30]}...")
                print()

    print()


def print_usage():
    print_banner()
    print("Usage:\n")
    print("  python main.py serve    Start API server")
    print("  python main.py auth     Authenticate provider")
    print("  python main.py list     List authenticated providers")
    print("  python main.py help     Show this help\n")


def main():
    if len(sys.argv) < 2:
        print_usage()
        return

    command = sys.argv[1].lower()

    if command == "serve":
        cmd_serve()
    elif command == "auth":
        cmd_auth()
    elif command == "list":
        cmd_list()
    elif command in ["help", "--help", "-h"]:
        print_usage()
    else:
        print(f"\n❌ Unknown command: {command}\n")
        print_usage()


if __name__ == "__main__":
    main()
