"""豆包（Doubao）流式响应处理器"""

import json
from typing import AsyncIterator, Optional
from zero_token.models import ChatCompletionChunk, StreamChoice, DeltaMessage


class DoubaoStreamHandler:
    def __init__(self, model: str):
        self.model = model
        self.first_sent = False
        self._last_text = ""

    async def process_stream(self, stream: AsyncIterator[str]) -> AsyncIterator[str]:
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
                    if data_str:
                        yield self._format_text_chunk(data_str)

    def _extract_text(self, data: dict) -> Optional[str]:
        choices = data.get("choices", [])
        if choices and isinstance(choices[0], dict):
            delta = choices[0].get("delta", {})
            if delta.get("content"):
                return delta["content"]
            if choices[0].get("text"):
                return choices[0]["text"]

        if data.get("text"):
            return data["text"]
        if data.get("response"):
            return data["response"]
        if data.get("content"):
            return data["content"]

        return None

    def _format_text_chunk(self, content: str) -> str:
        role = "assistant" if not self.first_sent else None
        self.first_sent = True

        chunk = ChatCompletionChunk(
            model=self.model,
            choices=[
                StreamChoice(
                    index=0,
                    delta=DeltaMessage(role=role, content=content),
                    finish_reason=None,
                )
            ],
        )

        return f"data: {chunk.model_dump_json()}\n\n"

    def _format_chunk(self, content: str = "", finish_reason: Optional[str] = None) -> str:
        return self._format_text_chunk(content) if content else f"data: [DONE]\n\n"
