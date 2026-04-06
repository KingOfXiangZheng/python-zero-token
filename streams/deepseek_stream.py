"""DeepSeek SSE 流式响应处理器 - 最终版本"""
import json
from typing import AsyncIterator, Optional
from zero_token.models import (
    ChatCompletionChunk,
    StreamChoice,
    DeltaMessage,
)


class DeepSeekStreamHandler:
    def __init__(self, model: str):
        self.model = model
        self.last_thinking = ""
        self.last_text = ""
        self.current_fragment_type = None
        self.first_text_sent = False
        self.processed_first_response = False
    
    async def process_stream(self, stream: AsyncIterator[str]) -> AsyncIterator[str]:
        async for line in stream:
            if not line.startswith("data: "):
                continue
            
            data_str = line[6:].strip()
            if data_str == "[DONE]":
                yield self._format_chunk("", finish_reason="stop")
                break
            
            try:
                data = json.loads(data_str)
                
                # 检查 fragment 类型
                new_type = self._check_fragment_type(data)
                if new_type and new_type != self.current_fragment_type:
                    self.current_fragment_type = new_type
                    
                    if new_type == "RESPONSE":
                        self.last_text = ""
                        self.processed_first_response = False
                    elif new_type in ["THINK", "THINKING"]:
                        self.last_thinking = ""
                
                # 提取
                if self.current_fragment_type in ["THINK", "THINKING"]:
                    delta = self._extract_thinking_delta(data)
                    if delta:
                        yield self._format_thinking_chunk(delta)
                elif self.current_fragment_type == "RESPONSE":
                    text = self._extract_text(data)
                    if text:
                        yield self._format_text_chunk(text)
                    
            except json.JSONDecodeError:
                pass
    
    def _check_fragment_type(self, data: dict) -> Optional[str]:
        if not isinstance(data, dict):
            return None
        
        # Initial fragments
        if isinstance(data.get("v"), dict):
            v_dict = data["v"]
            if isinstance(v_dict.get("response"), dict):
                response = v_dict["response"]
                fragments = response.get("fragments", [])
                if isinstance(fragments, list) and len(fragments) > 0:
                    last_frag = fragments[-1]
                    if isinstance(last_frag, dict):
                        return last_frag.get("type")
        
        # APPEND with array
        if data.get("o") == "APPEND" and isinstance(data.get("v"), list):
            for item in data["v"]:
                if isinstance(item, dict) and item.get("type"):
                    return item.get("type")
        
        return None
    
    def _extract_thinking_delta(self, data: dict) -> Optional[str]:
        if not isinstance(data, dict):
            return None
        
        # Initial fragments
        if isinstance(data.get("v"), dict):
            v_dict = data["v"]
            if isinstance(v_dict.get("response"), dict):
                response = v_dict["response"]
                fragments = response.get("fragments", [])
                if isinstance(fragments, list):
                    for frag in fragments:
                        if isinstance(frag, dict) and frag.get("type") in ["THINK", "THINKING"]:
                            content = frag.get("content", "")
                            if isinstance(content, str) and content:
                                if len(content) > len(self.last_thinking):
                                    delta = content[len(self.last_thinking):]
                                    self.last_thinking = content
                                    return delta
                                elif content != self.last_thinking:
                                    self.last_thinking = ""
                                    return content
        
        # APPEND and simple v
        if isinstance(data.get("v"), str):
            v = data["v"]
            if len(v) > len(self.last_thinking):
                delta = v[len(self.last_thinking):]
                self.last_thinking = v
                return delta
            elif v != self.last_thinking:
                self.last_thinking = ""
                return v
        
        return None
    
    def _extract_text(self, data: dict) -> Optional[str]:
        if not isinstance(data, dict):
            return None
        
        # Format 1: Initial fragments
        if isinstance(data.get("v"), dict):
            v_dict = data["v"]
            if isinstance(v_dict.get("response"), dict):
                response = v_dict["response"]
                fragments = response.get("fragments", [])
                if isinstance(fragments, list):
                    full_text = ""
                    for frag in fragments:
                        if isinstance(frag, dict) and frag.get("type") == "RESPONSE":
                            content = frag.get("content", "")
                            if isinstance(content, str):
                                full_text += content
                    if full_text and not self.processed_first_response:
                        self.processed_first_response = True
                        self.last_text = full_text
                        return full_text
        
        # Format 2: APPEND with array
        if data.get("o") == "APPEND" and isinstance(data.get("v"), list):
            for item in data["v"]:
                if isinstance(item, dict) and item.get("type") == "RESPONSE":
                    content = item.get("content", "")
                    if isinstance(content, str) and content:
                        return content
        
        # Format 3: APPEND with string
        if data.get("o") == "APPEND" and isinstance(data.get("v"), str):
            return data["v"]
        
        # Format 4: Simple v string
        if isinstance(data.get("v"), str):
            return data["v"]
        
        return None
    
    def _format_thinking_chunk(self, thinking: str) -> str:
        chunk = ChatCompletionChunk(
            model=self.model,
            choices=[
                StreamChoice(
                    index=0,
                    delta=DeltaMessage(role=None, content=None),
                    finish_reason=None,
                )
            ],
        )
        chunk_dict = chunk.model_dump(mode="json")
        chunk_dict["choices"][0]["delta"]["reasoning_content"] = thinking
        return f"data: {json.dumps(chunk_dict, ensure_ascii=False)}\n\n"
    
    def _format_text_chunk(self, content: str) -> str:
        role = "assistant" if not self.first_text_sent else None
        self.first_text_sent = True
        
        chunk = ChatCompletionChunk(
            model=self.model,
            choices=[
                StreamChoice(
                    index=0,
                    delta=DeltaMessage(
                        role=role,
                        content=content,
                    ),
                    finish_reason=None,
                )
            ],
        )
        return f"data: {chunk.model_dump_json()}\n\n"
    
    def _format_chunk(self, content: str = "", finish_reason: Optional[str] = None) -> str:
        return self._format_text_chunk(content) if content else f"data: {ChatCompletionChunk(model=self.model, choices=[StreamChoice(index=0, delta=DeltaMessage(), finish_reason=finish_reason)]).model_dump_json()}\n\n"
