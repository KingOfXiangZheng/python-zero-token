"""GLM Web API 客户端 - 修复版本"""
import hashlib
import json
import uuid
import httpx
from typing import Optional, AsyncIterator
from zero_token.models import AuthCredentials

ASSISTANT_ID_MAP = {"glm-4-plus": "65940acff94777010aa6b796", "glm-4": "65940acff94777010aa6b796"}
DEFAULT_ASSISTANT_ID = "65940acff94777010aa6b796"
SIGN_SECRET = "8a1317a7468aa3ad86e997d08f3f31cb"
X_EXP_GROUPS = "na_android_config:exp:NA,na_4o_config:exp:4o_A,tts_config:exp:tts_config_a,na_glm4plus_config:exp:open,mainchat_server_app:exp:A,mobile_history_daycheck:exp:a,desktop_toolbar:exp:A,chat_drawing_server:exp:A,drawing_server_cogview:exp:cogview4,app_welcome_v2:exp:A,chat_drawing_streamv2:exp:A,mainchat_rm_fc:exp:add,mainchat_dr:exp:open,chat_auto_entrance:exp:A,drawing_server_hi_dream:control:A,homepage_square:exp:close,assistant_recommend_prompt:exp:3,app_home_regular_user:exp:A,memory_common:exp:enable,mainchat_moe:exp:300,assistant_greet_user:exp:greet_user,app_welcome_personalize:exp:A,assistant_model_exp_group:exp:glm4.5,ai_wallet:exp:ai_wallet_enable"


class GlmClient:
    def __init__(self, credentials):
        self.credentials = credentials
        self.base_url = "https://chatglm.cn"
        self.device_id = uuid.uuid4().hex
        self.conversation_id = None
        self.access_token = None
        self._cookies = None
    
    def _generate_sign(self):
        import time
        e = int(time.time() * 1000)
        A = str(e)
        t = len(A)
        o = [int(c) for c in A]
        i = sum(o) - o[t - 2]
        a = i % 10
        timestamp = A[:t-2] + str(a) + A[t-1:]
        nonce = uuid.uuid4().hex
        sign_str = f"{timestamp}-{nonce}-{SIGN_SECRET}"
        sign = hashlib.md5(sign_str.encode()).hexdigest()
        return {"timestamp": timestamp, "nonce": nonce, "sign": sign}
    
    def _parse_cookies(self):
        if self._cookies:
            return self._cookies
        cookies = {}
        for part in self.credentials.cookie.split(';'):
            if '=' in part:
                name, value = part.strip().split('=', 1)
                cookies[name.strip()] = value.strip()
        self._cookies = cookies
        return self._cookies
    
    async def refresh_access_token(self):
        cookies = self._parse_cookies()
        refresh_token = cookies.get('chatglm_refresh_token')
        access_token = cookies.get('chatglm_token')
        
        if refresh_token and not self.access_token:
            sign = self._generate_sign()
            request_id = uuid.uuid4().hex.replace('-', '')
            
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {refresh_token}",
                "App-Name": "chatglm",
                "X-App-Platform": "pc",
                "X-App-Version": "0.0.1",
                "X-Device-Id": self.device_id,
                "X-Request-Id": request_id,
                "X-Sign": sign["sign"],
                "X-Nonce": sign["nonce"],
                "X-Timestamp": sign["timestamp"],
            }
            
            async with httpx.AsyncClient() as client:
                try:
                    resp = await client.post(
                        f"{self.base_url}/chatglm/user-api/user/refresh",
                        headers=headers,
                        json={},
                        timeout=10
                    )
                    if resp.status_code == 200:
                        data = resp.json()
                        new_token = data.get("result", {}).get("access_token") or data.get("result", {}).get("accessToken") or data.get("accessToken")
                        if new_token:
                            self.access_token = new_token
                            print(f"[GLM] Token refreshed successfully")
                            return
                except Exception as e:
                    print(f"[GLM] Refresh failed: {e}")
        
        if not self.access_token and access_token:
            self.access_token = access_token
    
    async def chat_completion_stream(self, message, model="glm-4-plus"):
        await self.refresh_access_token()
        
        if not self.access_token:
            raise Exception("No access token available")
        
        assistant_id = ASSISTANT_ID_MAP.get(model, DEFAULT_ASSISTANT_ID)
        sign = self._generate_sign()
        request_id = uuid.uuid4().hex
        
        body = {
            "assistant_id": assistant_id,
            "conversation_id": self.conversation_id or "",
            "project_id": "",
            "chat_type": "user_chat",
            "meta_data": {
                "cogview": {"rm_label_watermark": False},
                "is_test": False,
                "input_question_type": "xxxx",
                "channel": "",
                "draft_id": "",
                "chat_mode": "zero",
                "is_networking": False,
                "quote_log_id": "",
                "platform": "pc",
            },
            "messages": [{"role": "user", "content": [{"type": "text", "text": message}]}],
        }
        
        cookies = self._parse_cookies()
        headers = {
            "Content-Type": "application/json",
            "Accept": "text/event-stream",
            "Authorization": f"Bearer {self.access_token}",
            "App-Name": "chatglm",
            "Origin": "https://chatglm.cn",
            "X-App-Platform": "pc",
            "X-App-Version": "0.0.1",
            "X-App-fr": "default",
            "X-Device-Brand": "",
            "X-Device-Id": self.device_id,
            "X-Device-Model": "",
            "X-Exp-Groups": X_EXP_GROUPS,
            "X-Lang": "zh",
            "X-Nonce": sign["nonce"],
            "X-Request-Id": request_id,
            "X-Sign": sign["sign"],
            "X-Timestamp": sign["timestamp"],
            "Cookie": self.credentials.cookie,
            "User-Agent": self.credentials.user_agent,
        }
        
        async with httpx.AsyncClient(timeout=120.0) as client:
            async with client.stream(
                "POST",
                f"{self.base_url}/chatglm/backend-api/assistant/stream",
                headers=headers,
                json=body,
            ) as response:
                if response.status_code != 200:
                    error = await response.aread()
                    print(f"[GLM] Error {response.status_code}: {error.decode()}")
                    response.raise_for_status()
                
                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        data_str = line[6:].strip()
                        if data_str == "[DONE]":
                            yield "data: [DONE]\n\n"
                            break
                        yield f"data: {data_str}\n\n"
                        
                        try:
                            data = json.loads(data_str)
                            if isinstance(data, dict) and data.get("conversation_id"):
                                self.conversation_id = data["conversation_id"]
                        except:
                            pass
