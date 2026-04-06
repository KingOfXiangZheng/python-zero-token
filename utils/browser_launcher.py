"""浏览器启动工具"""

import os
import sys
import subprocess
import platform
from typing import Optional
from pathlib import Path


class BrowserLauncher:
    """浏览器启动器"""

    CHROME_PATHS = {
        "Windows": [
            r"C:\Program Files\Google\Chrome\Application\chrome.exe",
            r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
            os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe"),
        ],
        "Darwin": [
            "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
            "/Applications/Chromium.app/Contents/MacOS/Chromium",
        ],
        "Linux": [
            "/usr/bin/google-chrome",
            "/usr/bin/google-chrome-stable",
            "/usr/bin/chromium-browser",
            "/usr/bin/chromium",
            "/snap/bin/chromium",
        ],
    }

    @classmethod
    def find_chrome(cls) -> Optional[str]:
        """查找系统上的 Chrome 可执行文件"""
        system = platform.system()
        paths = cls.CHROME_PATHS.get(system, [])

        for path in paths:
            if os.path.exists(path):
                return path

        try:
            if system == "Windows":
                result = subprocess.run(
                    ["where", "chrome"],
                    capture_output=True,
                    text=True,
                    timeout=2
                )
                if result.returncode == 0:
                    return result.stdout.split('\n')[0].strip()
            else:
                result = subprocess.run(
                    ["which", "google-chrome", "chromium", "chromium-browser"],
                    capture_output=True,
                    text=True,
                    timeout=2
                )
                if result.returncode == 0:
                    return result.stdout.split('\n')[0].strip()
        except Exception:
            pass

        return None

    @classmethod
    def start_chrome(
        cls,
        cdp_port: int = 9222,
        user_data_dir: str = "chrome-debug-profile",
        headless: bool = False
    ) -> Optional[subprocess.Popen]:
        """
        启动 Chrome 浏览器（带远程调试）

        Args:
            cdp_port: CDP 端口号
            user_data_dir: 用户数据目录
            headless: 是否无头模式

        Returns:
            subprocess.Popen 对象，如果启动失败返回 None
        """
        chrome_path = cls.find_chrome()

        if not chrome_path:
            print("❌ 未找到 Chrome 浏览器")
            print("\n请安装 Chrome 或手动指定路径:")
            print("  Windows: C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe")
            print("  macOS: /Applications/Google Chrome.app/Contents/MacOS/Google Chrome")
            print("  Linux: /usr/bin/google-chrome")
            return None

        user_data_dir = os.path.abspath(user_data_dir)

        args = [
            chrome_path,
            f"--remote-debugging-port={cdp_port}",
            f"--user-data-dir={user_data_dir}",
        ]

        if headless:
            args.append("--headless=new")

        os.makedirs(user_data_dir, exist_ok=True)

        try:
            print(f"🚀 正在启动 Chrome...")
            print(f"   路径: {chrome_path}")
            print(f"   CDP 端口: {cdp_port}")
            print(f"   用户数据目录: {user_data_dir}")

            process = subprocess.Popen(
                args,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                creationflags=subprocess.CREATE_NO_WINDOW if platform.system() == "Windows" else 0
            )

            import time
            import httpx

            max_wait = 10
            for i in range(max_wait):
                try:
                    response = httpx.get(
                        f"http://127.0.0.1:{cdp_port}/json/version",
                        timeout=1
                    )
                    if response.status_code == 200:
                        print(f"✓ Chrome 已启动 (CDP: {cdp_port})")
                        return process
                except Exception:
                    time.sleep(1)

            print(f"❌ Chrome 启动超时")
            process.terminate()
            return None

        except Exception as e:
            print(f"❌ 启动 Chrome 失败: {e}")
            return None

        # 确保 user_data_dir 是绝对路径
        user_data_dir = os.path.abspath(user_data_dir)

        # Chrome 启动参数
        args = [
            chrome_path,
            f"--remote-debugging-port={cdp_port}",
            f"--user-data-dir={user_data_dir}",
        ]

        if headless:
            args.append("--headless=new")

        # 首次启动时创建目录
        os.makedirs(user_data_dir, exist_ok=True)

        try:
            print(f"🚀 正在启动 Chrome...")
            print(f"   路径: {chrome_path}")
            print(f"   CDP 端口: {cdp_port}")
            print(f"   用户数据目录: {user_data_dir}")

            process = subprocess.Popen(
                args,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                creationflags=subprocess.CREATE_NO_WINDOW
                if platform.system() == "Windows"
                else 0,
            )

            # 等待 Chrome 启动
            import time
            import httpx

            max_wait = 10
            for i in range(max_wait):
                try:
                    response = httpx.get(
                        f"http://127.0.0.1:{cdp_port}/json/version", timeout=1
                    )
                    if response.status_code == 200:
                        print(f"✓ Chrome 已启动 (CDP: {cdp_port})")
                        return process
                except Exception:
                    time.sleep(1)

            print(f"❌ Chrome 启动超时")
            process.terminate()
            return None

        except Exception as e:
            print(f"❌ 启动 Chrome 失败: {e}")
            return None

    @classmethod
    def check_cdp_available(cls, cdp_port: int = 9222) -> bool:
        """检查 CDP 端口是否可用"""
        try:
            import httpx

            response = httpx.get(f"http://127.0.0.1:{cdp_port}/json/version", timeout=2)
            return response.status_code == 200
        except Exception:
            return False


def ensure_chrome_running(
    cdp_port: int = 9222,
    user_data_dir: str = "chrome-debug-profile",
    auto_start: bool = True,
) -> bool:
    """
    确保 Chrome 正在运行（带 CDP）

    Args:
        cdp_port: CDP 端口号
        user_data_dir: 用户数据目录
        auto_start: 如果 Chrome 未运行，是否自动启动

    Returns:
        Chrome 是否正在运行
    """
    if BrowserLauncher.check_cdp_available(cdp_port):
        print(f"✓ Chrome 已运行 (CDP: {cdp_port})")
        return True

    if auto_start:
        process = BrowserLauncher.start_chrome(cdp_port, user_data_dir)
        return process is not None

    return False
