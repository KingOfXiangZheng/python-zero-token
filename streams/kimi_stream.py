"""Kimi SSE 流式响应处理器"""

import json
from typing import AsyncIterator, Optional
from zero_token.models import (
    ChatCompletionChunk,
    StreamChoice,
    DeltaMessage,
)


class KimiStreamHandler:
    """Kimi 流式响应处理器"""

    def __init__(self, model: str):
        self.model = model
        self.last_text = ""
        self.first_text_sent = False

    async def process_stream(self, stream: AsyncIterator[str]) -> AsyncIterator[str]:
        """处理 SSE 流并转换为 OpenAI 格式"""
        async for line in stream:
            if line.startswith("data: "):
                data_str = line[6:].strip()

                if data_str == "[DONE]":
                    yield self._format_chunk("", finish_reason="stop")
                    break

                try:
                    data = json.loads(data_str)
                    text = self._extract_text(data)
                    if text:
                        yield self._format_text_chunk(text)
                except json.JSONDecodeError:
                    pass

    def _extract_text(self, data: dict) -> Optional[str]:
        """从响应数据中提取内容"""
        # Kimi 可能返回的格式：
        # {"data": {"content": "text"}}
        # {"event": "text", "data": "text"}

        if isinstance(data.get("data"), dict):
            content = data["data"].get("content")
            if isinstance(content, str):
                return content

        if isinstance(data.get("data"), str):
            return data["data"]

        if isinstance(data.get("text"), str):
            return data["text"]

        if isinstance(data.get("content"), str):
            return data["content"]

        return None

    def _format_text_chunk(self, content: str) -> str:
        """格式化为 OpenAI chunk 格式"""
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
        return self._format_text_chunk(content) if content else f"data: [DONE]\n\n"
