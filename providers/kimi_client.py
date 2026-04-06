"""Kimi Web API Client - 使用正确的域名和认证"""

import asyncio
import json
from typing import AsyncIterator
from zero_token.models import AuthCredentials


class KimiClient:
    def __init__(self, credentials):
        self.credentials = credentials
        self.base_url = "https://www.kimi.com"
        self.page = None
        self.browser = None

    async def chat_completion_stream(self, message, model="kimi"):
        if not self.page:
            await self._connect_to_page()

        print(f"[Kimi] Sending message...")
        print(f"[Kimi] Using base_url: {self.base_url}")

        result = await self._send_message(message, model)

        if not result.get("ok"):
            error = result.get("error", "Unknown error")
            print(f"[Kimi] Error: {error}")
            error_json = json.dumps({"error": {"message": error, "type": "invalid_request_error"}})
            yield f"data: {error_json}\n\n"
            yield "data: [DONE]\n\n"
            return

        result_text = result.get("text", "")
        if result_text:
            print(f"[Kimi] Got response: {len(result_text)} chars")
            yield f'data: {{"text": {json.dumps(result_text)}}}\n\n'
        else:
            print(f"[Kimi] Empty response")

        yield "data: [DONE]\n\n"

    async def _send_message(self, message, model="kimi"):
        return await self.page.evaluate(
            """
            async ({ baseUrl, message, authToken, scenario }) => {
                console.log("[Kimi Browser] Starting...");
                console.log("[Kimi Browser] Base URL:", baseUrl);
                console.log("[Kimi Browser] Token available:", authToken ? "yes" : "no");
                
                if (!authToken) {
                    return { ok: false, error: "No auth token provided" };
                }
                
                const req = {
                    scenario: scenario,
                    message: {
                        role: "user",
                        blocks: [{ message_id: "", text: { content: message } }],
                        scenario: scenario,
                    },
                    options: { thinking: false },
                };
                
                const enc = new TextEncoder().encode(JSON.stringify(req));
                const buf = new ArrayBuffer(5 + enc.byteLength);
                const dv = new DataView(buf);
                dv.setUint8(0, 0x00);
                dv.setUint32(1, enc.byteLength, false);
                new Uint8Array(buf, 5).set(enc);
                
                try {
                    const res = await fetch(baseUrl + "/apiv2/kimi.gateway.chat.v1.ChatService/Chat", {
                        method: "POST",
                        headers: {
                            "Content-Type": "application/connect+json",
                            "Connect-Protocol-Version": "1",
                            Accept: "*/*",
                            Origin: baseUrl,
                            Referer: baseUrl + "/",
                            "X-Language": "zh-CN",
                            "X-Msh-Platform": "web",
                            Authorization: "Bearer " + authToken,
                        },
                        body: buf,
                    });
                    
                    console.log("[Kimi Browser] Status:", res.status);
                    
                    if (!res.ok) {
                        const errorText = await res.text();
                        console.log("[Kimi Browser] Error response:", errorText.substring(0, 200));
                        return { ok: false, error: errorText.substring(0, 500) };
                    }
                    
                    const arr = await res.arrayBuffer();
                    const u8 = new Uint8Array(arr);
                    const texts = [];
                    let o = 0;
                    
                    while (o + 5 <= u8.length) {
                        const len = new DataView(u8.buffer, u8.byteOffset + o + 1, 4).getUint32(0, false);
                        if (o + 5 + len > u8.length) break;
                        const chunk = u8.slice(o + 5, o + 5 + len);
                        try {
                            const obj = JSON.parse(new TextDecoder().decode(chunk));
                            if (obj.error) {
                                return { ok: false, error: obj.error.message };
                            }
                            if (obj.block?.text?.content && ["set", "append"].includes(obj.op || "")) {
                                texts.push(obj.block.text.content);
                            }
                            if (obj.done) break;
                        } catch (e) {
                            // parse error
                        }
                        o += 5 + len;
                    }
                    
                    console.log("[Kimi Browser] Text chunks:", texts.length);
                    return { ok: true, text: texts.join("") };
                    
                } catch (e) {
                    console.error("[Kimi Browser] Exception:", e);
                    return { ok: false, error: "Exception: " + String(e) };
                }
            }
            """,
            {
                "baseUrl": self.base_url,
                "message": message,
                "authToken": self.credentials.bearer,
                "scenario": self._get_scenario(model),
            },
        )

    def _get_scenario(self, model):
        if "search" in model:
            return "SCENARIO_SEARCH"
        elif "research" in model:
            return "SCENARIO_RESEARCH"
        elif "k1" in model:
            return "SCENARIO_K1"
        else:
            return "SCENARIO_K2"

    async def _connect_to_page(self):
        from playwright.async_api import async_playwright

        print("[Kimi] Connecting to browser...")
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

            kimi_page = None
            for page_ in ctx.pages:
                url_lower = page_.url.lower()
                if "kimi.com" in url_lower or "moonshot.cn" in url_lower:
                    kimi_page = page_
                    print(f"[Kimi] Found existing page: {page_.url}")
                    break

            if kimi_page:
                self.page = kimi_page
            else:
                self.page = await ctx.new_page()
                await self.page.goto(self.base_url, wait_until="domcontentloaded")
                print("[Kimi] Created new page")
                await asyncio.sleep(3)

        except Exception as e:
            print(f"[Kimi] Connection failed: {e}")
            raise


async def main():
    from zero_token.models import AuthCredentials

    creds = AuthCredentials(cookie="", bearer="test_token", user_agent="test")
    client = KimiClient(creds)

    async for chunk in client.chat_completion_stream("Hello", "kimi"):
        print(chunk)


if __name__ == "__main__":
    asyncio.run(main())
