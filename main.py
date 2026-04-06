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


def print_banner():
    print('''
========================================
  Zero Token API Server
  Free LLM API via browser automation
========================================
    ''')


def cmd_serve():
    print_banner()
    print(f'Server running on http://{settings.host}:{settings.port}')
    print(f'Docs: http://{settings.host}:{settings.port}/docs')
    print("\nRun 'python main.py auth' first if no credentials\n")
    start_server()


def cmd_auth():
    print_banner()
    print("Starting authentication...\n")
    
    providers = auth_storage.list_providers()
    if providers:
        print("Existing providers:")
        for p in providers:
            print(f"  - {p}")
        print()
    
    print("Select provider to authenticate:")
    print("  1. DeepSeek")
    print("  2. GLM (智谱)")
    print("  3. Kimi (月之暗面)")
    print("  4. 豆包 (Doubao)")
    print()
    
    choice = input("Enter option (1-4): ").strip()
    
    if choice == "1":
        auth = DeepSeekAuth()
        credentials = asyncio.run(auth.login(cdp_port=9222))
        if credentials:
            print(f"\n✅ Auth success!")
            print(f"   Cookie length: {len(credentials.cookie)}")
            if credentials.bearer:
                print(f"   Bearer: {credentials.bearer[:30]}...")
            print(f"\nCredentials saved: {settings.auth_file}")
            print("Now run 'python main.py serve'\n")
    
    elif choice == "2":
        auth = GlmAuth()
        credentials = asyncio.run(auth.login(cdp_port=9222))
        if credentials:
            print(f"\n✅ Auth success!")
            print(f"   Cookie length: {len(credentials.cookie)}")
            print(f"\nCredentials saved: {settings.auth_file}")
            print("Now run 'python main.py serve'\n")
    
    elif choice == "3":
        auth = KimiAuth()
        credentials = asyncio.run(auth.login(cdp_port=9222))
        if credentials:
            print(f"\n✅ Auth success!")
            print(f"   Cookie length: {len(credentials.cookie)}")
            print(f"\nCredentials saved: {settings.auth_file}")
            print("Now run 'python main.py serve'\n")
    
    elif choice == "4":
        auth = DoubaoAuth()
        credentials = asyncio.run(auth.login(cdp_port=9222))
        if credentials:
            print(f"\n✅ Auth success!")
            print(f"   Cookie length: {len(credentials.cookie)}")
            print(f"\nCredentials saved: {settings.auth_file}")
            print("Now run 'python main.py serve'\n")
    
    else:
        print("\n❌ Invalid option\n")


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
