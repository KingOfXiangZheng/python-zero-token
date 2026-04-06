from fastapi import FastAPI, HTTPException, Header
from fastapi.responses import StreamingResponse
from typing import Optional, AsyncIterator
import json
from zero_token.models import *
from zero_token.config import settings, PROVIDER_CONFIGS
from utils.storage import auth_storage


app = FastAPI(title="Zero Token API", description="Free LLM API via browser automation", version="0.1.0")


@app.get("/")
async def root():
    return {"message": "Zero Token API", "version": "0.1.0", "docs": "/docs"}


@app.get("/v1/models")
async def list_models():
    models = []
    for provider_id, config in PROVIDER_CONFIGS.items():
        for model_id in config.get("models", {}).keys():
            models.append(ModelInfo(id=f"{provider_id}/{model_id}", owned_by=provider_id))
    return ModelList(data=models)


@app.post("/v1/chat/completions")
async def chat_completions(request: ChatCompletionRequest, authorization: Optional[str] = Header(None)):
    provider, model = _parse_model(request.model)
    
    credentials = auth_storage.get_credentials(provider)
    if not credentials:
        raise HTTPException(status_code=401, detail=f"No credentials for {provider}. Run 'python main.py auth' first.")
    
    messages = _format_messages(request.messages)
    
    if request.stream:
        return StreamingResponse(_stream_response(provider, model, credentials, messages, request), media_type="text/event-stream")
    else:
        return await _non_stream_response(provider, model, credentials, messages, request)


async def _stream_response(provider, model, credentials, messages, request):
    try:
        if provider == "deepseek":
            from providers.deepseek_client import DeepSeekClient
            from streams.deepseek_stream import DeepSeekStreamHandler
            client = DeepSeekClient(credentials)
            handler = DeepSeekStreamHandler(model)
            stream = client.chat_completion_stream(messages, model=model, search_enabled=False)
        elif provider == "glm":
            from providers.glm_client import GlmClient
            from streams.glm_stream import GlmStreamHandler
            client = GlmClient(credentials)
            handler = GlmStreamHandler(model)
            stream = client.chat_completion_stream(messages, model=model)
        elif provider == "kimi":
            from providers.kimi_client import KimiClient
            from streams.kimi_stream import KimiStreamHandler
            client = KimiClient(credentials)
            handler = KimiStreamHandler(model)
            stream = client.chat_completion_stream(messages, model=model)
        elif provider == "doubao":
            from providers.doubao_client import DoubaoClient
            from streams.doubao_stream import DoubaoStreamHandler
            client = DoubaoClient(credentials)
            handler = DoubaoStreamHandler(model)
            stream = client.chat_completion_stream(messages, model=model)
        else:
            error = {"error": {"message": f"Unsupported provider: {provider}", "type": "invalid_request_error"}}
            yield f"data: {error}\n\n"
            return
        
        async for chunk in handler.process_stream(stream):
            yield chunk
    
    except Exception as e:
        print(f"[Server] Stream error: {e}")
        error = {"error": {"message": str(e), "type": "internal_error"}}
        yield f"data: {json.dumps(error)}\n\n"


async def _non_stream_response(provider, model, credentials, messages, request):
    try:
        accumulated = ""
        
        if provider == "deepseek":
            from providers.deepseek_client import DeepSeekClient
            client = DeepSeekClient(credentials)
            stream = client.chat_completion_stream(messages, model=model)
        elif provider == "glm":
            from providers.glm_client import GlmClient
            client = GlmClient(credentials)
            stream = client.chat_completion_stream(messages, model=model)
        elif provider == "kimi":
            from providers.kimi_client import KimiClient
            client = KimiClient(credentials)
            stream = client.chat_completion_stream(messages, model=model)
        elif provider == "doubao":
            from providers.doubao_client import DoubaoClient
            client = DoubaoClient(credentials)
            stream = client.chat_completion_stream(messages, model=model)
        else:
            raise HTTPException(status_code=404, detail=f"Provider {provider} not supported")
        
        async for line in stream:
            if line.startswith("data: ") and line != "data: [DONE]\n\n":
                try:
                    data = json.loads(line[6:])
                    if isinstance(data.get("v"), str):
                        accumulated += data["v"]
                    if isinstance(data.get("text"), str):
                        accumulated += data["text"]
                    if isinstance(data.get("content"), str):
                        accumulated += data["content"]
                    if isinstance(data.get("response"), str):
                        accumulated += data["response"]
                except:
                    pass
        
        if not accumulated:
            accumulated = "(No response)"
        
        return ChatCompletionResponse(model=model, choices=[ChatCompletionChoice(index=0, message=ChatMessage(role="assistant", content=accumulated), finish_reason="stop")])
    
    except Exception as e:
        print(f"[Server] Non-stream error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


def _parse_model(model_id):
    if "/" in model_id:
        parts = model_id.split("/", 1)
        return parts[0], parts[1]
    return settings.default_provider, model_id


def _format_messages(messages):
    formatted = []
    for msg in messages:
        content = msg.content if isinstance(msg.content, str) else str(msg.content)
        formatted.append(f"{msg.role}: {content}")
    return "\n\n".join(formatted)


def start_server():
    import uvicorn
    uvicorn.run("zero_token.server:app", host=settings.host, port=settings.port, reload=settings.debug)
