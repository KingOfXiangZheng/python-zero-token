"""凭证存储工具"""

import json
from pathlib import Path
from typing import Dict, Optional
from zero_token.models import AuthCredentials
from zero_token.config import settings


class AuthStorage:
    """凭证存储管理"""

    def __init__(self, file_path: Optional[str] = None):
        self.file_path = Path(file_path or settings.auth_file)
        self._ensure_file()

    def _ensure_file(self):
        if not self.file_path.exists():
            self._save({})

    def _load(self) -> Dict:
        try:
            with open(self.file_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}

    def _save(self, data: Dict):
        with open(self.file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2, default=str)

    def save_credentials(self, provider: str, credentials: AuthCredentials):
        data = self._load()
        data[provider] = credentials.model_dump()
        self._save(data)

    def get_credentials(self, provider: str) -> Optional[AuthCredentials]:
        data = self._load()
        if provider in data:
            return AuthCredentials(**data[provider])
        return None

    def delete_credentials(self, provider: str):
        data = self._load()
        if provider in data:
            del data[provider]
            self._save(data)

    def list_providers(self) -> list:
        data = self._load()
        return list(data.keys())


auth_storage = AuthStorage()
