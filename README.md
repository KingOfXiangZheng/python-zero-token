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

#### 方式一：浏览器认证（推荐）

```bash
python main.py auth
```

程序会自动：
1. 启动 Chrome（如果未运行）
2. 打开所有 4 个平台的登录页面
3. 提示你在浏览器中登录各平台
4. 按 Enter 键后自动捕获所有平台的凭证

#### 方式二：账号密码认证（Linux 服务器）

```bash
python main.py account
```

选择平台，输入账号密码即可自动认证。支持：
- DeepSeek
- GLM（智谱）

#### 方式三：导入凭证

```bash
python main.py import
```

从其他机器导出凭证文件，在服务器上导入使用。

```bash
# 在有界面机器上导出
python main.py export

# 复制 credentials.json 到服务器
# 在服务器上导入
python main.py import
```

**实际运行示例：**

```
========================================
  Zero Token API Server
  Free LLM API via browser automation
========================================

Starting authentication...

Checking Chrome status...
✓ Chrome 已运行 (CDP: 9222)

需要登录的平台:
  - DeepSeek
  - GLM (智谱)
  - Kimi (月之暗面)
  - 豆包 (Doubao)

🚀 正在打开登录页面...
请在浏览器中完成登录，然后按 Enter 键继续...

  Opening DeepSeek: https://chat.deepseek.com
  Opening GLM (智谱): https://chatglm.cn
  Opening Kimi (月之暗面): https://www.kimi.com
  Opening 豆包 (Doubao): https://www.doubao.com

✓ 已打开 4 个登录页面

==================================================
请在浏览器中完成所有平台的登录
登录完成后，按 Enter 键继续捕获凭证...
==================================================
```

在浏览器中完成所有平台的登录后，按 Enter 键继续：

```
🔄 开始捕获凭证...

正在捕获 DeepSeek 凭证...
正在连接到 Chrome (CDP: 9222)...
✓ 已连接到 Chrome
正在检查 DeepSeek 登录状态...
✓ 检测到已登录状态
正在捕获凭证...
正在触发 API 请求...
✓ 捕获到 Bearer Token
✓ 捕获到 Bearer Token
✓ 从响应中捕获到 Token
✓ 捕获到 Cookies (5 个)
  ✅ 认证成功!
     Cookie 长度: 317
     Bearer: PHvTIz0vCe/Ta670qw4FFkb+xFF3dj...

正在捕获 GLM (智谱) 凭证...
正在连接到 Chrome (CDP: 9222)...
✓ 已连接到 Chrome
正在检查 GLM 登录状态...
✓ 检测到已登录状态
正在捕获凭证...
✓ 捕获到 Cookies (8 个)
✓ chatglm_refresh_token: eyJhbGciOiJIUzI1NiIsInR5cCI6Ik...
✓ chatglm_token: eyJhbGciOiJIUzI1NiIsInR5cCI6Ik...
  ✅ 认证成功!
     Cookie 长度: 1546
     Bearer: eyJhbGciOiJIUzI1NiIsInR5cCI6Ik...

正在捕获 Kimi (月之暗面) 凭证...
连接到 Chrome (CDP: 9222)...
✓ 已连接到 Chrome
正在检查 Kimi 登录状态...
✓ 检测到已登录状态
正在捕获凭证...
总共捕获 57 个 cookies
  ✓ 找到 kimi-auth cookie
✓ Cookie 长度：5796
✓ Bearer token：eyJhbGciOiJIUzUxMiIsInR5cCI6Ik...
  ✅ 认证成功!
     Cookie 长度: 5796
     Bearer: eyJhbGciOiJIUzUxMiIsInR5cCI6Ik...

正在捕获 豆包 (Doubao) 凭证...
连接到 Chrome (CDP: 9222)...
✓ 已连接到 Chrome
正在检查豆包登录状态...
✓ 检测到已登录状态
正在捕获凭证...
总共捕获 57 个 cookies
  找到：hook_slardar_session_id=20260406203032A64E7CA443A10501...
  找到：ds_session_id=7f685f9dea3a446989904b60d34d85...
  找到：passport_auth_status=98a4d8f091bb32b04e03e1f4330241...
✓ Cookie 长度：5796
✓ Bearer: 98a4d8f091bb32b04e03e1f4330241...
  ✅ 认证成功!
     Cookie 长度: 5796
     Bearer: 98a4d8f091bb32b04e03e1f4330241...

==================================================
凭证捕获完成!
  ✅ 成功: 4 个平台
  ❌ 失败: 0 个平台
  凭证文件: .auth.json
==================================================

现在可以运行 'python main.py serve' 启动服务
```

### 3. 启动 API 服务

```bash
python main.py serve
```

**实际运行示例：**

```
========================================
  Zero Token API Server
  Free LLM API via browser automation
========================================

Server running on http://0.0.0.0:8000
Docs: http://0.0.0.0:8000/docs

Run 'python main.py auth' first if no credentials

INFO:     Started server process [111504]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
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

# 浏览器认证（自动打开所有平台，批量捕获凭证）
python main.py auth

# 账号密码认证（Linux 服务器推荐）
python main.py account

# 从文件导入凭证
python main.py import

# 导出凭证到文件
python main.py export

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
CHROME_HEADLESS=false                        # 无头模式（Linux 服务器推荐）

# 服务器配置
HOST=0.0.0.0                                # 监听地址
PORT=8000                                    # 监听端口

# 凭证存储
AUTH_FILE=.auth.json                         # 凭证文件路径
```

### 无头模式（Headless）

适用于 Linux 服务器等无界面环境：

```env
CHROME_HEADLESS=true
```

启用后 Chrome 将在后台运行，不显示图形界面。

> ⚠️ **注意**：无头模式下仍需要手动登录，详见 [Linux 认证指南](docs/LINUX_AUTH.md)

### Linux 服务器认证

对于无界面环境，推荐以下方案：

1. **导入凭证**（推荐）：在有界面机器完成认证，将 `.auth.json` 复制到服务器
2. **无头模式 + Xvfb**：使用虚拟显示环境
3. **远程调试**：连接到其他机器的浏览器实例

详细说明请参考 [Linux 认证指南](docs/LINUX_AUTH.md)

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