# Python Zero Token

**Free LLM API Service** - Browser automation for zero-cost API-free LLM calls

## Features

- Zero Cost: Browser login, no API tokens needed
- OpenAI Compatible: /v1/chat/completions endpoint
- Streaming: SSE streaming support
- Credentials: Auto capture and store
- Multi-Platform: DeepSeek, GLM, Kimi

## Supported Models

| Platform | Status | Models |
|----------|--------|--------|
| DeepSeek | Full support | deepseek-chat, deepseek-reasoner |
| GLM | Full support | glm-4-plus, glm-4, glm-4-think |
| Kimi | Full support | kimi |

## Quick Start

1. Install: pip install -r requirements.txt and playwright install chromium
2. Start Chrome: chrome.exe --remote-debugging-port=9222 --user-data-dir=chrome-debug-profile
3. Auth: python main.py auth
4. Start Server: python main.py serve

## Usage

`python
import openai

client = openai.OpenAI(
    api_key="dummy",
    base_url="http://localhost:8000/v1"
)

# DeepSeek streaming
response = client.chat.completions.create(
    model="deepseek/deepseek-chat",
    messages=[{"role": "user", "content": "Hello!"}],
    stream=True
)

for chunk in response:
    if chunk.choices[0].delta.content:
        print(chunk.choices[0].delta.content, end="", flush=True)

# GLM streaming
response = client.chat.completions.create(
    model="glm/glm-4-plus",
    messages=[{"role": "user", "content": "Introduce yourself"}],
    stream=True
)

# Kimi
response = client.chat.completions.create(
    model="kimi/kimi",
    messages=[{"role": "user", "content": "Hello!"}],
    stream=True
)
`

## Project Structure

`
python-zero-token/
├── providers/           # Auth and API clients
│   ├── deepseek_*.py   # DeepSeek (PoW+WASM)
│   ├── glm_*.py        # GLM (MD5 signature)
│   └── kimi_*.py       # Kimi (browser automation)
├── streams/            # Stream handlers
│   ├── deepseek_stream.py
│   ├── glm_stream.py
│   └── kimi_stream.py
├── zero_token/         # Core modules
│   ├── config.py       # Configuration
│   ├── models.py       # Data models
│   └── server.py       # FastAPI server
├── utils/
│   └── storage.py      # Credential storage
├── main.py             # Main entry
├── requirements.txt    # Dependencies
└── README.md          # This file
`

## Technical Implementation

- **DeepSeek**: PoW algorithm with DeepSeekHashV1 WASM module
- **GLM**: MD5 signature (timestamp-nonce-secret)
- **Kimi**: Browser automation with Connect protocol

## Notes

1. Credentials expire periodically - re-authenticate as needed
2. Keep Chrome running during use
3. Web endpoints may have rate limits
4. For research/learning only - follow platform ToS

## License

MIT License
