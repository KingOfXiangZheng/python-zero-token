"""DeepSeek Web API 客户端 - 最终版本"""
import hashlib, json, base64, pathlib, struct, httpx
from typing import Optional, AsyncIterator, Dict, Any
import httpx
from zero_token.models import AuthCredentials
from wasmtime import Store, Module, Instance, Memory


class DeepSeekClient:
    def __init__(self, credentials: AuthCredentials):
        self.credentials = credentials
        self.base_url = "https://chat.deepseek.com/api/v0"
        self.session_id: Optional[str] = None
        self.parent_message_id: Optional[str] = None
        self.wasm_module = None
        self.wasm_store = None
        self.wasm_instance = None
    
    def _get_headers(self) -> Dict[str, str]:
        return {
            "Cookie": self.credentials.cookie,
            "User-Agent": self.credentials.user_agent,
            "Content-Type": "application/json",
            "Accept": "*/*",
            "Authorization": f"Bearer {self.credentials.bearer}" if self.credentials.bearer else "",
            "Referer": "https://chat.deepseek.com/",
            "Origin": "https://chat.deepseek.com",
            "x-client-platform": "web",
            "x-client-version": "1.7.0",
        }
    
    async def create_session(self) -> str:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/chat_session/create", 
                headers=self._get_headers(), 
                json={}
            )
            response.raise_for_status()
            data = response.json()
            self.session_id = (
                data.get("data", {}).get("biz_data", {}).get("id") 
                or data.get("data", {}).get("biz_data", {}).get("chat_session_id")
                or data.get("data", {}).get("biz_data", {}).get("biz_id")
            )
            return self.session_id
    
    async def chat_completion_stream(
        self, message: str, model: str = "deepseek-chat", search_enabled: bool = False
    ) -> AsyncIterator[str]:
        if not self.session_id:
            await self.create_session()
            print(f"[DeepSeek] Created session: {self.session_id}")

        pow_response = await self._solve_pow("/api/v0/chat/completion")
        print(f"[DeepSeek] PoW solved: {len(pow_response)} bytes")

        payload = {
            "chat_session_id": self.session_id,
            "parent_message_id": self.parent_message_id,
            "prompt": message,
            "ref_file_ids": [],
            "thinking_enabled": "reasoner" in model,
            "search_enabled": search_enabled,
            "preempt": False,
        }

        headers = {**self._get_headers(), "x-ds-pow-response": pow_response}

        async with httpx.AsyncClient(timeout=60.0) as client:
            async with client.stream(
                "POST", 
                "https://chat.deepseek.com/api/v0/chat/completion", 
                headers=headers, 
                json=payload
            ) as response:
                if response.status_code != 200:
                    error_text = await response.aread()
                    print(f"[DeepSeek] Error {response.status_code}: {error_text.decode()}")
                    response.raise_for_status()

                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        data_str = line[6:]
                        if data_str == "[DONE]":
                            yield "data: [DONE]\n\n"
                            break
                        yield f"data: {data_str}\n\n"

                        try:
                            data = json.loads(data_str)
                            if "response_message_id" in data:
                                self.parent_message_id = data["response_message_id"]
                        except json.JSONDecodeError:
                            pass
    
    def _init_wasm(self):
        if self.wasm_instance is not None:
            return True
        
        try:
            wasm_path = pathlib.Path(__file__).parent.parent / "deepseek_hash.wasm"
            
            if not wasm_path.exists():
                print(f"[DeepSeek] WASM file not found: {wasm_path}")
                return False
            
            self.wasm_store = Store()
            self.wasm_module = Module.from_file(self.wasm_store.engine, str(wasm_path))
            self.wasm_instance = Instance(self.wasm_store, self.wasm_module, [])
            print(f"[DeepSeek] WASM module loaded successfully")
            return True
        except Exception as e:
            print(f"[DeepSeek] Failed to load WASM: {e}")
            return False

    async def _solve_pow(self, target_path: str) -> str:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/chat/create_pow_challenge",
                headers=self._get_headers(),
                json={"target_path": target_path},
            )
            
            data = response.json()

            challenge = (
                data.get("data", {}).get("biz_data", {}).get("challenge")
                or data.get("data", {}).get("challenge")
                or data.get("challenge")
            )

            if not challenge:
                print(f"[DeepSeek] No challenge in response")
                return ""

            algorithm = challenge.get("algorithm", "sha256")
            print(f"[DeepSeek] Solving PoW: {algorithm}")

            if algorithm == "sha256":
                answer = self._solve_sha256_pow(challenge)
                print(f"[DeepSeek] PoW answer (SHA256): {answer}")
            elif algorithm == "DeepSeekHashV1":
                answer = self._solve_deepseek_hash_v1(challenge)
                print(f"[DeepSeek] PoW answer (DeepSeekHashV1): {answer}")
            else:
                print(f"[DeepSeek] Unknown algorithm: {algorithm}")
                answer = 0

            # 修复：将 float 转换为 int
            answer_int = int(answer) if isinstance(answer, float) else answer
            
            pow_data = {**challenge, "answer": answer_int, "target_path": target_path}
            pow_json = json.dumps(pow_data, separators=(",", ":"))
            print(f"[DeepSeek] PoW data: {pow_json}")
            return base64.b64encode(pow_json.encode()).decode()
    
    def _solve_deepseek_hash_v1(self, challenge: Dict[str, Any]) -> int:
        if not self._init_wasm():
            return 0
        
        try:
            salt = challenge.get("salt", "")
            target = challenge.get("challenge", "")
            expire_at = challenge.get("expire_at", 0)
            difficulty = challenge.get("difficulty", 16)
            
            prefix = f"{salt}_{expire_at}_"
            
            exports = self.wasm_instance.exports(self.wasm_store)
            
            memory = None
            alloc = None
            add_to_stack = None
            wasm_solve = None
            
            for name, export in exports.items():
                if name == "memory":
                    memory = export
                elif name == "__wbindgen_export_0":
                    alloc = export
                elif name == "__wbindgen_add_to_stack_pointer":
                    add_to_stack = export
                elif name == "wasm_solve":
                    wasm_solve = export
            
            if not all([memory, alloc, add_to_stack, wasm_solve]):
                print(f"[DeepSeek] Missing WASM exports")
                return 0
            
            def encode_string(s):
                buf = s.encode("utf-8")
                ptr = alloc(self.wasm_store, len(buf), 1)
                memory.write(self.wasm_store, buf, ptr)
                return ptr, len(buf)
            
            ptr_c, len_c = encode_string(target)
            ptr_p, len_p = encode_string(prefix)
            retptr = add_to_stack(self.wasm_store, -16)
            
            wasm_solve(self.wasm_store, retptr, ptr_c, len_c, ptr_p, len_p, float(difficulty))
            
            result_bytes = memory.read(self.wasm_store, retptr, retptr + 16)
            status = int.from_bytes(result_bytes[0:4], "little", signed=True)
            answer_float = struct.unpack('<d', result_bytes[8:16])[0]
            
            add_to_stack(self.wasm_store, 16)
            
            if status == 0:
                print(f"[DeepSeek] WASM solve failed")
                return 0
            
            answer = int(answer_float)
            print(f"[DeepSeek] WASM solve success: {answer}")
            return answer
            
        except Exception as e:
            print(f"[DeepSeek] WASM error: {e}")
            import traceback
            traceback.print_exc()
            return 0

    def _solve_sha256_pow(self, challenge: Dict[str, Any]) -> int:
        target = challenge.get("challenge", "")
        salt = challenge.get("salt", "")
        difficulty = challenge.get("difficulty", 16)

        nonce = 0
        max_iterations = min(difficulty * 10000, 1000000)
        
        while nonce < max_iterations:
            input_str = f"{salt}{target}{nonce}"
            hash_result = hashlib.sha256(input_str.encode()).hexdigest()

            zero_bits = 0
            for char in hash_result:
                val = int(char, 16)
                if val == 0:
                    zero_bits += 4
                else:
                    zero_bits += 4 - (val.bit_length())
                    break

            if zero_bits >= difficulty:
                return nonce

            nonce += 1

        return 0
