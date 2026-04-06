"""GLM SSE 流式响应处理器"""

import json
from typing import AsyncIterator, Optional
from zero_token.models import (
    ChatCompletionChunk,
    StreamChoice,
    DeltaMessage,
)


class GlmStreamHandler:
    def __init__(self, model: str):
        self.model = model
        self.last_thinking = ""  # 上次发送的 thinking
        self.last_content = ""    # 上次发送的 content
    
    async def process_stream(self, stream: AsyncIterator[str]) -> AsyncIterator[str]:
        async for line in stream:
            if line.startswith("data: "):
                data_str = line[6:].strip()
                if data_str == "[DONE]":
                    yield self._format_chunk("", finish_reason="stop")
                    break
                
                try:
                    data = json.loads(data_str)
                    
                    # 提取 think 增量
                    thinking_delta = self._extract_thinking_delta(data)
                    if thinking_delta:
                        yield self._format_chunk_with_thinking(thinking_delta)
                    
                    # 提取 content 增量
                    content_delta = self._extract_content_delta(data)
                    if content_delta:
                        yield self._format_chunk_with_content(content_delta)
                
                except json.JSONDecodeError:
                    pass
    
    def _extract_thinking_delta(self, data: dict) -> Optional[str]:
        if not data.get("parts") or not isinstance(data["parts"], list):
            return None
        
        for part in data["parts"]:
            if not isinstance(part, dict):
                continue
            
            content_list = part.get("content", [])
            if not isinstance(content_list, list):
                continue
            
            for item in content_list:
                if isinstance(item, dict) and item.get("type") == "think":
                    think = item.get("think", "")
                    if think and isinstance(think, str):
                        if len(think) > len(self.last_thinking):
                            delta = think[len(self.last_thinking):]
                            self.last_thinking = think
                            return delta
        return None
    
    def _extract_content_delta(self, data: dict) -> Optional[str]:
        if not data.get("parts") or not isinstance(data["parts"], list):
            return None
        
        for part in data["parts"]:
            if not isinstance(part, dict):
                continue
            
            content_list = part.get("content", [])
            if not isinstance(content_list, list):
                continue
            
            for item in content_list:
                if isinstance(item, dict) and item.get("type") == "text":
                    text = item.get("text", "")
                    if text and isinstance(text, str):
                        if len(text) > len(self.last_content):
                            delta = text[len(self.last_content):]
                            self.last_content = text
                            return delta
        return None
    
    def _format_chunk_with_thinking(self, thinking: str) -> str:
        """格式化为带 thinking 的 chunk"""
        chunk = ChatCompletionChunk(
            model=self.model,
            choices=[
                StreamChoice(
                    index=0,
                    delta=DeltaMessage(
                        role=None,
                        content=None,
                    ),
                    finish_reason=None,
                )
            ],
        )
        # 使用 reasoning_content 字段（部分 OpenAI 兼容服务支持）
        chunk_dict = chunk.model_dump(mode="json")
        chunk_dict["choices"][0]["delta"]["reasoning_content"] = thinking
        return f"data: {json.dumps(chunk_dict, ensure_ascii=False)}\n\n"
    
    def _format_chunk_with_content(self, content: str) -> str:
        """格式化为带 content 的 chunk"""
        chunk = ChatCompletionChunk(
            model=self.model,
            choices=[
                StreamChoice(
                    index=0,
                    delta=DeltaMessage(
                        role=None,
                        content=content,
                    ),
                    finish_reason=None,
                )
            ],
        )
        return f"data: {chunk.model_dump_json()}\n\n"
