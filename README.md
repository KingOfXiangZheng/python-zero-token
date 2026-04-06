# Python Zero Token

**零令牌 LLM API 服务** - 通过浏览器自动化实现零成本、无需 API 密钥的 LLM 调用

## ✨ 功能特性

- 🆓 **完全免费**：使用浏览器登录，无需购买 API 密钥
- 🔄 **OpenAI 兼容**：提供标准化的 `/v1/chat/completions` 接口
- 📡 **流式传输**：支持 SSE（Server-Sent Events）流式响应
- 🔐 **自动凭证管理**：自动捕获并存储登录 Cookie 和 Token
- 🌐 **多平台支持**：DeepSeek、智谱 GLM、Kimi（月之暗面）、豆包
- 🚀 **一键认证**：自动打开所有平台登录页面，批量捕获凭证
- 💾 **持久化登录**：浏览器数据持久化，无需重复登录

## 🤖 支持的模型

| 平台 | 状态 | 可用模型 |
|----------|--------|--------|
| DeepSeek | ✅ 完全支持 | deepseek-chat、deepseek-reasoner |
| 智谱 GLM | ✅ 完全支持 | glm-4-plus、glm-4、glm-4-think |
| Kimi | ✅ 完全支持 | kimi |
| 豆包 | ✅ 完全支持 | doubao-pro-4k、doubao-lite-4k |

## 🚀 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
playwright install chromium
```

### 2. 一键认证

```bash
python main.py auth
```

程序会自动：
1. 启动 Chrome（如果未运行）
2. 打开所有 4 个平台的登录页面
3. 提示你在浏览器中登录各平台
4. 按 Enter 键后自动捕获所有平台的凭证

### 3. 启动 API 服务

```bash
python main.py serve
```

服务将运行在 `http://localhost:8000`，API 文档可访问 `http://localhost:8000/docs`

## 📝 使用示例

### Python OpenAI SDK

```python
import openai

# 创建客户端（使用虚拟 API Key）
client = openai.OpenAI(
    api_key="dummy",  # 可以是任意值
    base_url="http://localhost:8000/v1"
)

# DeepSeek 流式调用
response = client.chat.completions.create(
    model="deepseek/deepseek-chat",
    messages=[{"role": "user", "content": "你好！请介绍一下自己"}],
    stream=True
)

for chunk in response:
    if chunk.choices[0].delta.content:
        print(chunk.choices[0].delta.content, end="", flush=True)
```

### GLM 智谱调用

```python
# GLM-4 Plus 流式调用
response = client.chat.completions.create(
    model="glm/glm-4-plus",
    messages=[{"role": "user", "content": "写一段 Python 代码实现快速排序"}],
    stream=True
)

for chunk in response:
    if chunk.choices[0].delta.content:
        print(chunk.choices[0].delta.content, end="", flush=True)
```

### Kimi 月之暗面调用

```python
# Kimi 调用
response = client.chat.completions.create(
    model="kimi/kimi",
    messages=[{"role": "user", "content": "解释量子计算的基本原理"}],
    stream=True
)

for chunk in response:
    if chunk.choices[0].delta.content:
        print(chunk.choices[0].delta.content, end="", flush=True)
```

### 豆包调用

```python
# 豆包调用
response = client.chat.completions.create(
    model="doubao/doubao-pro-4k",
    messages=[{"role": "user", "content": "帮我写一个产品介绍文案"}],
    stream=True
)

for chunk in response:
    if chunk.choices[0].delta.content:
        print(chunk.choices[0].delta.content, end="", flush=True)
```

### cURL 示例

```bash
curl -X POST http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer dummy" \
  -d '{
    "model": "deepseek/deepseek-chat",
    "messages": [
      {"role": "user", "content": "你好"}
    ],
    "stream": true
  }'
```

## 📂 项目结构

```
python-zero-token/
├── providers/           # 认证和 API 客户端
│   ├── deepseek_*.py   # DeepSeek（PoW+WASM 算法）
│   ├── glm_*.py        # GLM（MD5 签名）
│   ├── kimi_*.py       # Kimi（浏览器自动化）
│   └── doubao_*.py     # 豆包（浏览器自动化）
├── streams/            # 流式响应处理器
│   ├── deepseek_stream.py
│   ├── glm_stream.py
│   ├── kimi_stream.py
│   └── doubao_stream.py
├── zero_token/         # 核心模块
│   ├── config.py       # 配置管理
│   ├── models.py       # 数据模型
│   └── server.py       # FastAPI 服务器
├── utils/
│   ├── storage.py      # 凭证存储
│   └── browser_launcher.py  # 浏览器启动工具
├── main.py             # 主入口
├── requirements.txt    # 依赖列表
└── README.md          # 本文件
```

## 🔧 技术实现

- **DeepSeek**：使用 PoW（工作量证明）算法配合 DeepSeekHashV1 WASM 模块
- **GLM 智谱**：MD5 签名机制（timestamp-nonce-secret）
- **Kimi 月之暗面**：浏览器自动化 + Connect 协议
- **豆包**：浏览器自动化 + WebSocket 通信

## 🛠️ 命令说明

```bash
# 启动 API 服务器
python main.py serve

# 登录认证（自动打开所有平台，批量捕获凭证）
python main.py auth

# 查看已认证的平台列表
python main.py list

# 显示帮助信息
python main.py help
```

## ⚙️ 配置选项

可以通过环境变量或 `.env` 文件配置：

```env
# Chrome 配置
CHROME_USER_DATA_DIR=C:\tmp\chrome-debug    # 浏览器数据目录（持久化登录）
CHROME_CDP_PORT=9222                         # Chrome 调试端口
AUTO_START_CHROME=true                       # 自动启动 Chrome

# 服务器配置
HOST=0.0.0.0                                # 监听地址
PORT=8000                                    # 监听端口

# 凭证存储
AUTH_FILE=.auth.json                         # 凭证文件路径
```

## ⚠️ 注意事项

1. **凭证有效期**：各平台的 Cookie 和 Token 可能会过期，需要定期重新认证
2. **持久化登录**：登录状态保存在 `CHROME_USER_DATA_DIR` 目录中，首次认证后无需重复登录
3. **速率限制**：Web 端接口可能有速率限制，请合理使用
4. **仅供学习**：本项目仅供研究学习使用，请遵守各平台的服务条款

## 📜 许可证

MIT License

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

---

**免责声明**：本项目仅供学习和研究使用，请勿用于商业用途。使用本项目产生的任何后果由使用者自行承担。