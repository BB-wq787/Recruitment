# Railway 部署指南

## 📋 前置准备

### 1. 注册 Railway 账户
访问 [Railway.app](https://railway.app) 并注册账户

### 2. 安装 Railway CLI (可选)
```bash
npm install -g @railway/cli
railway login
```

### 3. 准备代码
确保以下文件存在：
- `App.py` - 主应用文件
- `requirements.txt` - 依赖列表
- `Procfile` - 启动命令
- `runtime.txt` - Python版本
- `templates/` - HTML模板
- `static/` - 静态文件

## 🚀 部署步骤

### 方法1: GitHub 集成 (推荐)

1. **连接 GitHub**
   - 登录 Railway Dashboard
   - 点击 "New Project"
   - 选择 "Deploy from GitHub repo"

2. **选择仓库**
   - 搜索并选择你的 `Recruitment` 仓库
   - 点击 "Deploy"

3. **等待部署**
   - Railway 会自动检测 Python 项目
   - 安装依赖并启动应用

### 方法2: Railway CLI

```bash
# 登录 Railway
railway login

# 初始化项目
railway init

# 部署
railway up
```

## 🗄️ 数据库配置详解

### Railway PostgreSQL 数据库添加步骤

#### 方法1: 在 Railway Dashboard 中添加 (推荐)

1. **登录 Railway Dashboard**
   - 访问 [railway.app](https://railway.app)
   - 登录你的账户

2. **进入你的项目**
   - 点击你创建的 Flask 项目
   - 确保项目已经从 GitHub 部署成功

3. **添加 PostgreSQL 数据库**
   ```
   项目页面 → 右侧面板点击 "+" 按钮 → "Database" → "Add PostgreSQL"
   ```
   或
   ```
   项目页面 → "Add" 按钮 → "Database" → "PostgreSQL"
   ```

4. **等待数据库创建**
   - Railway 会自动创建 PostgreSQL 实例
   - 这通常需要 1-2 分钟
   - 创建完成后，你会在项目面板中看到 PostgreSQL 图标

5. **配置数据库连接**
   - Railway 会**自动设置** `DATABASE_URL` 环境变量
   - 你的 Flask 应用会自动使用这个连接字符串
   - **无需手动配置任何环境变量**

#### 方法2: 使用 Railway CLI 添加数据库

```bash
# 确保你已经登录并在项目目录中
railway login
railway link  # 连接到现有项目

# 添加 PostgreSQL 数据库
railway add postgresql

# 查看环境变量
railway variables
```

### 数据库连接验证

添加数据库后，你的 Flask 应用会：

1. **自动检测 PostgreSQL** - 检查 `DATABASE_URL` 环境变量
2. **创建数据库表** - 运行 `init_db()` 函数
3. **迁移数据** - 从 SQLite 迁移现有数据（如有）

### 查看数据库信息

在 Railway Dashboard 中：

1. **点击 PostgreSQL 插件**
2. **查看 "Variables" 标签页** - 看到 `DATABASE_URL`
3. **查看 "Data" 标签页** - 可以浏览数据库内容
4. **查看 "Settings" 标签页** - 数据库配置选项

### 数据库管理

#### 备份数据库
- Railway 自动每日备份 PostgreSQL 数据库
- 你可以在 "Settings" → "Backups" 中管理备份

#### 重置数据库
如果需要重置数据库：
```
PostgreSQL 插件 → "Settings" → "Reset Database"
⚠️ 这将删除所有数据！
```

#### 数据库迁移
当你更新代码中的数据库结构时：
1. Railway 会自动重新部署应用
2. 你的 `init_db()` 函数会处理表创建和迁移

### 故障排除

#### 数据库连接问题
```bash
# 查看应用日志
railway logs

# 检查环境变量
railway variables

# 常见问题：
# 1. DATABASE_URL 未设置 - 确保 PostgreSQL 插件已添加
# 2. 连接超时 - 检查数据库状态
# 3. 权限问题 - Railway 自动处理，无需担心
```

### 环境变量

Railway 会自动设置：
- `DATABASE_URL` - PostgreSQL 连接字符串
- `PORT` - 应用端口

## 🔧 故障排除

### 常见问题

**1. 应用无法启动**
```bash
# 检查日志
railway logs

# 常见原因：
# - requirements.txt 缺少依赖
# - 数据库连接问题
# - 端口配置错误
```

**2. 数据库连接失败**
- 确保 PostgreSQL 插件已添加
- 检查 DATABASE_URL 环境变量
- 验证数据库表已创建

**3. 静态文件无法访问**
- 确保文件在 `static/` 目录中
- 检查 Flask 静态文件配置

### 调试技巧

```bash
# 查看应用日志
railway logs

# 进入应用容器 (如果可用)
railway run bash

# 检查环境变量
railway variables
```

## 📊 成本估算

Railway 每月免费额度：
- **$5 额度** - 足够运行小型 Flask 应用
- **数据库** - PostgreSQL 每月约 $1-2
- **带宽** - 每月 512GB 免费

**预计每月成本**: $1-3

## 🔄 更新部署

代码推送后，Railway 会自动重新部署：

```bash
git add .
git commit -m "Update application"
git push origin main
```

Railway 会检测到更改并自动部署新版本。

## 🌐 访问应用

部署完成后，Railway 会提供一个 URL:
```
https://your-app-name.up.railway.app
```

## 📞 支持

如果遇到问题：
1. 查看 Railway 文档
2. 检查应用日志
3. 联系 Railway 支持

---

**注意**: Railway 的免费额度每月刷新，适合长期运行的小型应用。
