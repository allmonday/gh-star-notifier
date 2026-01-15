# GitHub Star 通知器

当你的 GitHub 仓库被 star 时接收推送通知。

## 功能特性

- 🔔 **推送通知**：当有人 star 你的仓库时即时收到通知
- 🔒 **安全 Webhook 验证**：HMAC-SHA256 签名验证
- 📋 **仓库白名单**：只允许配置的仓库触发通知
- 🌐 **PWA 支持**：可在支持的设备上安装为原生应用
- 🧪 **测试通知**：发送测试通知验证设置
- 💾 **持久化存储**：使用 SQLite 管理订阅

## 架构

```
GitHub Webhook → 后端 (FastAPI) → 推送服务 → 浏览器 (PWA)
                      ↓
                 SQLite 数据库
```

## 技术栈

- **后端**：FastAPI + Python 3.11
- **前端**：Quasar Framework (Vue 3) + PWA
- **推送协议**：Web Push API + VAPID
- **数据库**：SQLite
- **部署**：Docker Compose

## 快速开始

### 前置要求

- Docker 和 Docker Compose
- （可选）Node.js 18+ 用于本地开发
- （可选）Python 3.11+ 用于本地开发

### 1. 克隆仓库

```bash
git clone <your-repo-url>
cd github-star-notifier
```

### 2. 配置环境变量

```bash
# 复制环境变量模板
cp .env.example .env

# 生成 VAPID 密钥
python backend/generate_vapid_keys.py --save

# 编辑 .env 添加其余配置
nano .env
```

必需的环境变量：

```bash
# VAPID 密钥（通过上述脚本自动生成）
VAPID_PRIVATE_KEY=your_vapid_private_key_here
VAPID_PUBLIC_KEY=your_vapid_public_key_here
VAPID_SUBJECT=mailto:your-email@example.com

# GitHub Webhook 密钥（使用以下命令生成：openssl rand -hex 32）
WEBHOOK_SECRET=your_webhook_secret_here

# 仓库白名单（允许的仓库列表，JSON 数组格式）
WEBHOOK_WHITELIST=["owner/repo1", "owner/repo2"]
```

**💡 提示**：运行以下命令可自动生成并保存 VAPID 密钥到 `.env` 文件：
```bash
python backend/generate_vapid_keys.py --save
```

或在线生成：https://vapidkeys.com/

### 3. 使用 Docker Compose 启动

```bash
docker-compose up -d
```

应用将在以下地址可用：
- 前端：http://localhost:5173
- 后端 API：http://localhost:8000
- API 文档：http://localhost:8000/docs

### 4. 订阅通知

1. 在浏览器中打开 http://localhost:5173
2. 点击"订阅推送通知"
3. 在弹出的提示中授予权限

### 5. 配置 GitHub Webhook

1. 在 GitHub 上打开你的仓库设置
2. 导航到 **Settings** → **Webhooks** → **Add webhook**
3. 配置 webhook：
   - **Payload URL**：`https://your-domain.com/api/webhook`
   - **Content type**：`application/json`
   - **Secret**：你的 `WEBHOOK_SECRET` 值
   - **Events**：选择 "Stars" → "Watch events"
4. 点击 "Add webhook"

## 本地开发（不使用 Docker）

### 后端

```bash
cd backend

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt

# 复制并编辑环境文件
cp .env.example .env

# 启动服务器
python main.py
```

后端将启动在 http://localhost:8000

### 前端

```bash
cd frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev
```

前端将启动在 http://localhost:8080

## API 端点

### 公开端点

- `GET /` - API 信息
- `GET /health` - 健康检查

### 订阅管理

- `GET /api/vapid-public-key` - 获取 VAPID 公钥
- `POST /api/subscribe` - 订阅推送通知
- `POST /api/unsubscribe` - 取消订阅
- `GET /api/subscriptions` - 获取所有活跃订阅

### 通知

- `POST /api/test-notification` - 发送测试通知
- `POST /api/webhook` - GitHub webhook 端点

## GitHub Webhook Payload

应用期望接收以下 GitHub webhook payload：

```json
{
  "action": "started",
  "repository": {
    "id": 123456789,
    "name": "my-repo",
    "full_name": "owner/my-repo",
    "description": "一个很棒的仓库",
    "html_url": "https://github.com/owner/my-repo",
    "stargazers_count": 42,
    "owner": {
      "login": "owner",
      "avatar_url": "https://github.com/owner.png"
    }
  },
  "sender": {
    "login": "user",
    "avatar_url": "https://github.com/user.png"
  },
  "starred_at": "2025-01-15T12:34:56Z"
}
```

## 安全性

### HMAC 验证

应用使用 HMAC-SHA256 验证 GitHub webhook 签名：

1. GitHub 在 `X-Hub-Signature-256` header 中发送签名
2. 应用使用 `WEBHOOK_SECRET` 计算期望的签名
3. 使用 constant-time 比较签名（防止时序攻击）
4. 无效签名将被拒绝（HTTP 403）

### 白名单

只有在 `WEBHOOK_WHITELIST` 中的仓库才能触发通知。在 `.env` 文件中配置：

```bash
WEBHOOK_WHITELIST=["owner/repo1", "owner/repo2"]
```

## 部署

### 使用 Caddy 进行生产部署

由于你已经配置了 Caddy 和 DDNS，可以将应用暴露在 5173 端口。

#### Caddyfile 示例

```
your-domain.com {
    reverse_proxy localhost:5173
}
```

#### Docker Compose 覆盖配置

创建 `docker-compose.override.yml`：

```yaml
version: '3.8'

services:
  frontend:
    ports:
      - "5173:80"

  backend:
    ports:
      - "8000:8000"
```

然后启动：

```bash
docker-compose up -d
```

### SSL/HTTPS

Web Push API 必需 HTTPS。配置 Caddy 自动获取 Let's Encrypt 证书：

```
your-domain.com {
    reverse_proxy localhost:5173

    # Caddy 自动处理 HTTPS
}
```

## 故障排除

### 收不到通知

1. **检查浏览器权限**：确保已允许通知
2. **检查浏览器控制台**：在开发者控制台中查看错误
3. **验证订阅**：在主页面检查订阅状态
4. **测试通知**：使用"发送测试通知"按钮

### Webhook 未触发

1. **检查 GitHub webhook 投递日志**：在仓库设置中查看
2. **验证 webhook 密钥**：确认与 `WEBHOOK_SECRET` 匹配
3. **检查仓库白名单**：确认仓库在 `WEBHOOK_WHITELIST` 中
4. **查看后端日志**：`docker-compose logs backend`

### Service Worker 问题

1. **注销旧的 service worker**：
   - 打开 DevTools → Application → Service Workers
   - 注销所有 service worker
2. **清除站点数据并刷新**
3. **检查 `/sw.js` 是否正确提供**

### 浏览器兼容性

| 浏览器 | 支持情况 |
|---------|---------|
| Chrome (桌面) | ✅ 完全支持 |
| Firefox (桌面) | ✅ 完全支持 |
| Chrome (Android) | ✅ 完全支持 |
| Safari (iOS 16.4+) | ⚠️ 有限支持 |
| Safari (macOS) | ❌ 不支持 |
| Edge (Windows) | ❌ 使用 WNS，不支持 VAPID |

## 项目结构

```
github-star-notifier/
├── backend/                      # FastAPI 后端
│   ├── main.py                   # FastAPI 应用入口
│   ├── database.py               # SQLite 数据库管理
│   ├── push_service.py           # 推送通知服务
│   ├── webhook_handler.py        # GitHub webhook 处理器
│   ├── models.py                 # Pydantic 模型
│   ├── requirements.txt          # Python 依赖
│   ├── Dockerfile                # 后端 Docker 镜像
│   └── .env.example              # 环境变量模板
├── frontend/                     # Quasar (Vue 3) 前端
│   ├── public/
│   │   ├── manifest.json         # PWA manifest
│   │   └── sw.js                 # Service Worker
│   ├── src/
│   │   ├── pages/IndexPage.vue   # 主页面
│   │   ├── composables/usePushNotification.js
│   │   └── ...
│   ├── package.json
│   ├── quasar.config.js
│   ├── Dockerfile                # 前端 Docker 镜像
│   └── nginx.conf                # Nginx 配置
├── docker-compose.yml            # Docker Compose 配置
├── .env.example                  # 环境变量模板
└── README.md                     # 本文件
```

## 使用说明

### 订阅流程

1. **访问应用**：在支持的浏览器中打开应用
2. **请求权限**：点击"订阅推送通知"按钮
3. **授予权限**：在浏览器弹窗中允许通知权限
4. **完成订阅**：系统将自动保存订阅信息

### 配置 GitHub Webhook

1. **生成密钥**：
   ```bash
   openssl rand -hex 32
   ```

2. **在 GitHub 配置 Webhook**：
   - 进入仓库 → Settings → Webhooks
   - 点击 "Add webhook"
   - 填写配置：
     - Payload URL: `https://your-domain.com/api/webhook`
     - Content type: `application/json`
     - Secret: 你的 `WEBHOOK_SECRET`
     - Events: 选择 "Stars"

3. **测试 Webhook**：
   - 在 GitHub webhook 页面点击 "Recent Deliveries"
   - 查看最近的投递记录和响应

### 发送测试通知

1. 确保已订阅推送通知
2. 在主页面找到"发送测试通知"卡片
3. 填写标题和消息内容
4. 点击"发送测试通知"按钮
5. 应该在几秒内收到通知

### 查看订阅状态

主页面显示：
- 当前订阅状态（已订阅/未订阅/权限被拒绝）
- 通知权限状态
- 订阅数量（如果有后端 API 访问）

## 常见问题

### Q: VAPID 密钥是什么？

A: VAPID (Voluntary Application Server Identification) 是 Web Push 协议的一部分，用于验证服务器身份。你需要生成一对密钥（公钥和私钥）：
- **公钥**：发送给浏览器，用于加密消息
- **私钥**：保存在服务器，用于签名

你可以：
1. 让应用在首次运行时自动生成（推荐）
2. 使用在线工具：https://vapidkeys.com/
3. 自己生成（见后端代码）

### Q: 为什么需要 HTTPS？

A: Web Push API 和 Service Worker 都要求 HTTPS。这是浏览器的安全限制。在开发环境中，`localhost` 可以豁免此要求。

### Q: 订阅会过期吗？

A: 是的。推送服务可能会撤销订阅，特别是如果长时间未使用。应用会处理 `410 Gone` 错误并自动清理过期订阅。

### Q: 如何备份订阅数据？

A: 订阅数据保存在 SQLite 数据库中（`backend/data/star_notifier.db`）。你可以定期备份这个文件。

### Q: 可以在多个设备上订阅吗？

A: 可以！每个设备的浏览器都会生成独立的订阅。只要你在这个设备上打开应用并订阅，就会在所有设备上收到通知。

## 许可证

MIT

## 作者

tangkikodo
