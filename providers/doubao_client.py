"""豆包（Doubao）客户端 - 使用samantha API格式"""

import asyncio
import json
import re
from typing import AsyncIterator
from zero_token.models import AuthCredentials
import uuid


class DoubaoClient:
    def __init__(self, credentials):
        self.credentials = credentials
        self.base_url = "https://www.doubao.com"
        self.page = None
        self.browser = None
        self.user_id = None
        self.conversation_id = None
        self.config = {}

    async def chat_completion_stream(self, message, model="doubao-pro-4k"):
        if not self.page:
            await self._connect_to_page()

        await asyncio.sleep(2)
        await self._extract_all_params()

        print(f"[豆包] 发送消息...")
        print(f"[豆包] 使用samantha API格式")

        result = await self._send_message_samantha(message, model)

        if not result:
            yield 'data: {"error": "Empty response"}\n\n'
            yield "data: [DONE]\n\n"
            return

        if isinstance(result, dict):
            if "error" in result:
                error = result["error"]
                print(f"[豆包] 错误：{error}")
                error_json = json.dumps({"error": {"message": error, "type": "api_error"}})
                yield f"data: {error_json}\n\n"
                yield "data: [DONE]\n\n"
                return

            if "event_type" in result:
                text = await self._parse_samantha_response(result)
                if text:
                    print(f"[豆包] 响应文本：{len(text)}chars")
                    yield f'data: {{"text": {json.dumps(text)}}}\n\n'
                yield "data: [DONE]\n\n"
                return

        if isinstance(result, str):
            async for text_chunk in self._stream_sse_chunks(result):
                if text_chunk:
                    yield f'data: {{"text": {json.dumps(text_chunk)}}}\n\n'

            yield "data: [DONE]\n\n"

    async def _extract_all_params(self):
        params_result = await self.page.evaluate("""
        () => {
            const result = {
                aid: '497858',
                device_platform: 'web',
                language: 'zh',
                pkg_type: 'release_version',
                real_aid: '497858',
                region: 'CN',
                samantha_web: '1',
                sys_region: 'CN',
                use_olympus_account: '1',
                version_code: '20800',
                device_id: '',
                fp: '',
                tea_uuid: '',
                web_tab_id: '',
                msToken: '',
                a_bogus: '',
            };
            
            try {
                const deviceId = localStorage.getItem('device_id');
                if (deviceId) result.device_id = deviceId;
                
                const fp = localStorage.getItem('fp') || localStorage.getItem('s_v_web_id');
                if (fp) result.fp = fp;
                
                const teaUuid = localStorage.getItem('tea_uuid');
                if (teaUuid) result.tea_uuid = teaUuid;
                
                const webTabId = localStorage.getItem('web_tab_id');
                if (webTabId) result.web_tab_id = webTabId;
            } catch(e) {}
            
            try {
                const urlParams = new URLSearchParams(window.location.search);
                const msToken = urlParams.get('msToken');
                if (msToken) result.msToken = msToken;
                
                const aBogus = urlParams.get('a_bogus');
                if (aBogus) result.a_bogus = aBogus;
            } catch(e) {}
            
            const cookies = document.cookie.split(';');
            for (const cookie of cookies) {
                const [name, value] = cookie.trim().split('=');
                if (name === 'sessionid') result.sessionid = value;
                if (name === 'ttwid') result.ttwid = value;
            }
            
            return result;
        }
        """)

        self.config = params_result
        print(
            f"[豆包] 提取参数：aid={params_result.get('aid')}, device_id={params_result.get('device_id', 'N/A')[:20]}"
        )
        print(f"[豆包] sessionid={params_result.get('sessionid', 'N/A')[:20]}")

    async def _send_message_samantha(self, message, model):
        import time

        query_params = self._build_query_params()
        url = f"{self.base_url}/samantha/chat/completion?{query_params}"

        local_conversation_id = f"local_16{str(int(time.time() * 1000))[-14:]}"
        local_message_id = str(uuid.uuid4())

        text = self._merge_messages_for_samantha([{"role": "user", "content": message}])

        request_body = {
            "messages": [
                {
                    "content": json.dumps({"text": text}),
                    "content_type": 2001,
                    "attachments": [],
                    "references": [],
                }
            ],
            "completion_option": {
                "is_regen": False,
                "with_suggest": True,
                "need_create_conversation": True,
                "launch_stage": 1,
                "is_replace": False,
                "is_delete": False,
                "message_from": 0,
                "event_id": "0",
            },
            "conversation_id": "0",
            "local_conversation_id": local_conversation_id,
            "local_message_id": local_message_id,
        }

        print(f"[豆包] 请求URL: {url[:80]}...")
        print(f"[豆包] local_conversation_id: {local_conversation_id}")

        js_code = f"""
        (async function() {{
            const url = "{url}";
            
            const requestBody = {json.dumps(request_body)};
            
            const headers = {{
                "Content-Type": "application/json",
                Accept: "text/event-stream",
                Referer: "https://www.doubao.com/chat/",
                Origin: "https://www.doubao.com",
                "Agw-js-conv": "str",
            }};
            
            const sessionid = "{self.config.get("sessionid", "")}";
            const ttwid = "{self.config.get("ttwid", "")}";
            if (sessionid) {{
                headers["Cookie"] = ttwid ? `sessionid=${{sessionid}}; ttwid=${{ttwid}}` : `sessionid=${{sessionid}}`;
            }}
            
            console.log("[豆包] URL:", url.substring(0, 80));
            console.log("[豆包] Headers keys:", Object.keys(headers));
            
            try {{
                const res = await fetch(url, {{
                    method: "POST",
                    headers: headers,
                    body: JSON.stringify(requestBody),
                }});
                
                console.log("[豆包] Status:", res.status);
                
                if (!res.ok) {{
                    const errorText = await res.text();
                    console.log("[豆包] Error:", errorText.substring(0, 500));
                    return {{ error: errorText.substring(0, 500) }};
                }}
                
                const allData = await res.text();
                console.log("[豆包] 响应长度:", allData.length);
                
                return allData;
                
            }} catch (e) {{
                console.error("[豆包] 异常:", e);
                return {{ error: "Exception: " + String(e) }};
            }}
        }})()
        """

        return await self.page.evaluate(js_code)

    def _build_query_params(self):
        params = []

        for key, value in self.config.items():
            if value and key not in ["msToken", "a_bogus", "sessionid", "ttwid"]:
                params.append(f"{key}={value}")

        if self.config.get("msToken"):
            params.append(f"msToken={self.config['msToken']}")
        if self.config.get("a_bogus"):
            params.append(f"a_bogus={self.config['a_bogus']}")

        return "&".join(params)

    def _merge_messages_for_samantha(self, messages):
        parts = []
        for m in messages:
            role = m.get("role", "user")
            content = m.get("content", "")
            parts.append(f"<|im_start|>{role}\n{content}\n")
        return "".join(parts) + "<|im_end|>\n"

    async def _parse_samantha_response(self, data):
        if data.get("code") is not None and data.get("code") != 0:
            return None

        if data.get("event_type") == 2003:
            return None

        if data.get("event_type") != 2001 or not data.get("event_data"):
            return None

        try:
            result = json.loads(data["event_data"])
            if result.get("is_finish"):
                return None

            message = result.get("message")
            if not message or message.get("content_type") not in [2001, 2008]:
                return None

            content_str = message.get("content")
            if content_str:
                content = json.loads(content_str)
                return content.get("text")
        except:
            pass

        return None

    async def _stream_sse_chunks(self, text):
        """流式生成SSE文本块"""
        for line in text.split("\n"):
            line = line.strip()

            if not line or not line.startswith("data: "):
                continue

            json_str = line[6:]
            if not json_str:
                continue

            try:
                event_wrapper = json.loads(json_str)

                event_type = event_wrapper.get("event_type")
                event_data_str = event_wrapper.get("event_data")

                if not event_data_str or event_type not in [2001, 2003]:
                    continue

                if event_type == 2003:
                    return

                event_data = json.loads(event_data_str)
                message = event_data.get("message", {})

                if message.get("is_finish"):
                    return

                content_str = message.get("content", "{}")
                if content_str and content_str != "{}":
                    content = json.loads(content_str)
                    text_chunk = content.get("text")
                    if text_chunk:
                        yield text_chunk

            except (json.JSONDecodeError, KeyError) as e:
                print(f"[豆包] 流式解析错误: {e}")
                continue

    async def _parse_sse_response(self, text):
        texts = []
        tts_content = None

        for line in text.split("\n"):
            line = line.strip()

            if not line or not line.startswith("data: "):
                continue

            json_str = line[6:]
            if not json_str:
                continue

            try:
                event_wrapper = json.loads(json_str)

                event_type = event_wrapper.get("event_type")
                event_data_str = event_wrapper.get("event_data")

                if not event_data_str or event_type not in [2001, 2003]:
                    continue

                if event_type == 2003:
                    break

                event_data = json.loads(event_data_str)
                message = event_data.get("message", {})

                if message.get("tts_content"):
                    tts_content = message["tts_content"]

                if message.get("is_finish"):
                    break

                content_str = message.get("content", "{}")
                if content_str and content_str != "{}":
                    content = json.loads(content_str)
                    text_chunk = content.get("text")
                    if text_chunk:
                        texts.append(text_chunk)

            except (json.JSONDecodeError, KeyError) as e:
                print(f"[豆包] 解析错误: {e}")
                continue

        if tts_content:
            return [tts_content]

        return texts

    async def _connect_to_page(self):
        from playwright.async_api import async_playwright

        print("[豆包] 正在连接浏览器...")
        p = await async_playwright().start()

        try:
            import httpx

            async with httpx.AsyncClient() as c:
                ws_url = (
                    (await c.get("http://127.0.0.1:9222/json/version"))
                    .json()
                    .get("webSocketDebuggerUrl")
                )

            if not ws_url:
                raise Exception("No WebSocket URL")

            self.browser = await p.chromium.connect_over_cdp(ws_url)
            ctx = self.browser.contexts[0]

            doubao_page = None
            for page_ in ctx.pages:
                if "doubao" in page_.url.lower() and "chat" in page_.url.lower():
                    doubao_page = page_
                    print(f"[豆包] 找到聊天页面：{page_.url}")
                    break

            if not doubao_page:
                for page_ in ctx.pages:
                    if "doubao" in page_.url.lower():
                        doubao_page = page_
                        print(f"[豆包] 找到豆包页面：{page_.url}")
                        break

            if doubao_page:
                self.page = doubao_page
            else:
                self.page = await ctx.new_page()
                await self.page.goto("https://www.doubao.com/chat/", wait_until="domcontentloaded")
                print("[豆包] 创建聊天页面")
                await asyncio.sleep(3)

        except Exception as e:
            print(f"[豆包] 连接失败：{e}")
            raise
