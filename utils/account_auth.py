"""账号密码认证工具"""

import httpx
import json
from typing import Optional, Dict
from utils.storage import auth_storage
from zero_token.models import AuthCredentials


class AccountAuth:
    """账号密码认证"""

    @staticmethod
    async def auth_deepseek(phone: str, password: str) -> Optional[AuthCredentials]:
        """
        DeepSeek 账号密码认证

        Args:
            phone: 手机号
            password: 密码

        Returns:
            AuthCredentials 对象，失败返回 None
        """
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                login_url = "https://chat.deepseek.com/api/v0/user/login"

                payload = {
                    "phone": phone,
                    "password": password,
                }

                headers = {
                    "Content-Type": "application/json",
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                }

                response = await client.post(login_url, json=payload, headers=headers)

                if response.status_code == 200:
                    data = response.json()
                    token = data.get("data", {}).get("biz_data", {}).get("token")

                    if token:
                        cookies = "; ".join(
                            [f"{k}={v}" for k, v in client.cookies.items()]
                        )
                        return AuthCredentials(
                            cookie=cookies,
                            bearer=token,
                            user_agent=headers["User-Agent"],
                        )
                else:
                    print(f"❌ 登录失败: {response.status_code}")
                    print(f"   {response.text}")

        except Exception as e:
            print(f"❌ 认证出错: {e}")

        return None

    @staticmethod
    async def auth_glm(account: str, password: str) -> Optional[AuthCredentials]:
        """
        GLM 账号密码认证

        Args:
            account: 账号（手机号或邮箱）
            password: 密码

        Returns:
            AuthCredentials 对象，失败返回 None
        """
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                login_url = "https://chatglm.cn/chatglm/backend-api/ pasa/login"

                payload = {
                    "username": account,
                    "password": password,
                }

                headers = {
                    "Content-Type": "application/json",
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                }

                response = await client.post(login_url, json=payload, headers=headers)

                if response.status_code == 200:
                    data = response.json()
                    token = data.get("result", {}).get("token")

                    if token:
                        cookies = "; ".join(
                            [f"{k}={v}" for k, v in client.cookies.items()]
                        )
                        return AuthCredentials(
                            cookie=cookies,
                            bearer=token,
                            user_agent=headers["User-Agent"],
                        )
                else:
                    print(f"❌ 登录失败: {response.status_code}")
                    print(f"   {response.text}")

        except Exception as e:
            print(f"❌ 认证出错: {e}")

        return None


def save_credentials_from_dict(credentials_dict: Dict[str, Dict[str, str]]):
    """
    从字典保存凭证

    Args:
        credentials_dict: 凭证字典，格式为
            {
                "deepseek": {"cookie": "...", "bearer": "..."},
                "glm": {"cookie": "...", "bearer": "..."},
                ...
            }
    """
    for provider, cred in credentials_dict.items():
        if "cookie" in cred:
            credentials = AuthCredentials(
                cookie=cred["cookie"],
                bearer=cred.get("bearer"),
                user_agent=cred.get("user_agent", "Mozilla/5.0"),
            )
            auth_storage.save_credentials(provider, credentials)
            print(f"✓ 已保存 {provider} 凭证")


def import_credentials_from_file(file_path: str):
    """
    从文件导入凭证

    Args:
        file_path: 凭证文件路径（JSON 格式）
    """
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            credentials_dict = json.load(f)

        save_credentials_from_dict(credentials_dict)
        print(f"\n✓ 凭证导入成功！")
        print(f"  文件: {file_path}")
    except Exception as e:
        print(f"❌ 导入失败: {e}")


def export_credentials_to_file(file_path: str):
    """
    导出凭证到文件

    Args:
        file_path: 输出文件路径
    """
    try:
        providers = auth_storage.list_providers()
        credentials_dict = {}

        for provider in providers:
            cred = auth_storage.get_credentials(provider)
            if cred:
                credentials_dict[provider] = {
                    "cookie": cred.cookie,
                    "bearer": cred.bearer,
                    "user_agent": cred.user_agent,
                }

        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(credentials_dict, f, indent=2, ensure_ascii=False)

        print(f"\n✓ 凭证导出成功！")
        print(f"  文件: {file_path}")
        print(f"  包含: {', '.join(credentials_dict.keys())}")
    except Exception as e:
        print(f"❌ 导出失败: {e}")
