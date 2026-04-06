# Linux 无界面环境认证指南

## 方案一：账号密码认证（推荐）

**最简单直接，无需任何界面**

### 使用方法

```bash
python main.py account
```

选择平台，输入账号密码即可自动认证。

**支持的平台：**
- DeepSeek
- GLM（智谱）

**示例：**

```bash
========================================
  Zero Token API Server
  Free LLM API via browser automation
========================================

Account Authentication

Select provider:
  1. DeepSeek
  2. GLM (智谱)

Enter option (1-2): 1
Account (phone/email): 13800138000
Password: ******

正在认证...
✓ DeepSeek 认证成功！
```

**优点：**
- ✅ 完全自动化，无需浏览器
- ✅ 无需 GUI 或虚拟显示
- ✅ 适合任何 Linux 环境
- ✅ 可以通过脚本自动化

**注意：**
- Kimi 和豆包暂不支持账号密码认证
- 部分平台可能有验证码或二次验证

---

## 方案二：导入凭证

适用于已有凭证的情况

### 1. 在有界面机器上导出凭证

```bash
# 使用浏览器认证
python main.py auth

# 完成所有登录后，导出凭证
python main.py export
```

### 2. 复制到服务器

```bash
scp credentials.json user@server:/path/to/python-zero-token/
```

### 3. 在服务器上导入

```bash
python main.py import

# 输入文件路径
Enter credentials file path: credentials.json

✓ 已保存 deepseek 凭证
✓ 已保存 glm 凭证
✓ 凭证导入成功！
  文件: credentials.json
```

---

## 方案三：使用无头模式（不推荐）

适用于需要 Kimi/豆包认证且没有其他选择的情况

### 1. 启用无头模式

创建 `.env` 文件：

```env
CHROME_HEADLESS=true
CHROME_USER_DATA_DIR=/tmp/chrome-debug
CHROME_CDP_PORT=9222
```

### 2. 安装 Xvfb（虚拟显示）

```bash
sudo apt-get install xvfb

# 启动 Xvfb
Xvfb :99 -screen 0 1920x1080x24 &
export DISPLAY=:99
```

### 3. 运行认证

```bash
python main.py auth
```

由于无头模式下看不到浏览器界面，需要：

#### 方法 A：使用 VNC 查看

```bash
# 安装 VNC 服务器
sudo apt-get install x11vnc

# 启动 VNC
x11vnc -display :99 -rfbport 5900

# 使用 VNC 客户端连接到 server:5900
```

#### 方法 B：使用 X11 转发

在本地机器上：

```bash
ssh -X user@server
cd /path/to/python-zero-token
python main.py auth
```

---

## 方案四：从有界面环境认证（原始方案）

如果上述方案都不可用

### 1. 在有界面的机器上认证

```bash
git clone <your-repo>
cd python-zero-token
pip install -r requirements.txt
playwright install chromium
python main.py auth
```

### 2. 复制凭证文件

```bash
# 方法 A：使用 export/import
python main.py export
scp credentials.json user@server:/path/

# 方法 B：直接复制 .auth.json
scp .auth.json user@server:/path/to/python-zero-token/
```

### 3. 在服务器上使用

```bash
python main.py serve
```

---

## 推荐方案对比

| 方案 | 优点 | 缺点 | 推荐度 |
|------|------|------|--------|
| 方案一（账号密码） | 最简单，完全自动化 | 部分平台不支持 | ⭐⭐⭐⭐⭐ |
| 方案二（导入凭证） | 简单可靠 | 需要先有凭证 | ⭐⭐⭐⭐ |
| 方案三（无头+Xvfb） | 支持所有平台 | 配置复杂，仍需要界面操作 | ⭐⭐ |
| 方案四（原始方案） | 支持所有平台 | 需要额外机器 | ⭐⭐⭐ |

---

## 实际使用建议

### 开发环境
使用浏览器认证（`python main.py auth`），简单直观。

### 生产环境

**首选：账号密码认证**
```bash
python main.py account
```

**备选：导入凭证**
1. 在开发机使用浏览器认证
2. 导出凭证文件
3. 在生产机导入

**多环境管理：**
```bash
# 开发环境
python main.py account
python main.py export
mv credentials.json credentials.dev.json

# 测试环境
python main.py account
python main.py export
mv credentials.json credentials.test.json

# 生产环境
python main.py import
# 输入: credentials.prod.json
```

---

## 凭证管理

### 加密存储

```python
import json
from cryptography.fernet import Fernet

# 生成密钥
key = Fernet.generate_key()
cipher = Fernet(key)

# 加密凭证
with open('credentials.json', 'r') as f:
    data = f.read()
encrypted = cipher.encrypt(data.encode())

with open('credentials.enc', 'wb') as f:
    f.write(encrypted)
```

### 环境变量存储（安全）

```bash
# 将凭证编码为 Base64
cat credentials.json | base64 -w 0 > credentials.b64

# 设置环境变量
export CREDENTIALS=$(cat credentials.b64)
```

```python
import os
import base64
import json
from utils.account_auth import save_credentials_from_dict

# 从环境变量读取
credentials_str = base64.b64decode(os.getenv('CREDENTIALS')).decode()
credentials_dict = json.loads(credentials_str)
save_credentials_from_dict(credentials_dict)
```

### 自动续期

```bash
# 添加到 crontab
0 0 */30 * * cd /path/to/python-zero-token && python main.py account
```

---

## 故障排查

### 账号密码认证失败

```bash
# 检查网络连接
curl -I https://chat.deepseek.com

# 检查账号密码是否正确
# 尝试在浏览器中登录验证

# 查看详细错误
python -c "
import asyncio
from utils.account_auth import AccountAuth
result = asyncio.run(AccountAuth.auth_deepseek('your_phone', 'your_password'))
print(result)
"
```

### 凭证导入失败

```bash
# 检查文件格式
cat credentials.json | python -m json.tool

# 验证凭证内容
python main.py list

# 手动测试导入
python -c "
from utils.account_auth import import_credentials_from_file
import_credentials_from_file('credentials.json')
"
```

### 无头模式问题

```bash
# 检查 Xvfb
ps aux | grep Xvfb

# 检查 DISPLAY
echo $DISPLAY

# 手动测试
google-chrome --headless=new --dump-dom https://www.google.com
```

---

## 安全建议

1. **不要在代码中硬编码账号密码**
2. **使用环境变量或配置文件管理敏感信息**
3. **定期更换密码**
4. **凭证文件设置正确的权限**：
   ```bash
   chmod 600 .auth.json
   chmod 600 credentials.json
   ```
5. **考虑使用密钥管理服务**（如 HashiCorp Vault、AWS Secrets Manager）