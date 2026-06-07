# MegaToken：AI 大模型 Token 价格看板

一个公开、非营利的 AI 大模型每百万 token 价格对比网站，支持实时价格查看和历史价格 K 线图分析。

## 在线访问

部署到 GitHub Pages 后，您的网站将通过以下地址访问：

```
https://您的用户名.github.io/MegaToken/
```

## 功能特点

- **实时价格看板**：显示各大云计算公司和 AI 大模型公司的 token 价格
- **价格对比**：支持按供应商、模型名称搜索和排序
- **货币切换**：支持美元/人民币切换显示
- **历史 K 线图**：查看各模型价格的历史走势
- **自动更新**：每周自动抓取最新价格数据
- **数据覆盖**：支持 35+ 个模型，涵盖 OpenAI、Anthropic、Google、Microsoft、AWS、DeepSeek 等厂商

## 技术栈

- **前端**：HTML5 + CSS3 + JavaScript + ECharts
- **后端**：Python + Playwright（数据抓取）
- **部署**：GitHub Pages + GitHub Actions

## 本地开发

### 1. 克隆仓库

```bash
git clone https://github.com/您的用户名/MegaToken.git
cd MegaToken
```

### 2. 启动本地服务器

```bash
python -m http.server 8000
```

访问 `http://localhost:8000` 查看效果。

### 3. 手动更新价格数据

```bash
python scripts/fetch_prices.py
```

### 4. 生成历史数据

```bash
python scripts/build_history.py
```

## 项目结构

```
.
├── index.html              # 实时价格看板
├── chart.html              # 历史价格 K 线图
├── pricing.json            # 当前定价数据
├── history.json            # 历史 OHLC 数据
├── history/                # 每日价格快照
├── scripts/
│   ├── fetch_prices.py     # 自动抓取价格脚本
│   └── build_history.py    # 生成历史数据脚本
├── .github/workflows/
│   └── update.yml          # GitHub Actions 自动更新和部署
└── README.md
```

## 数据来源

数据源自各厂商官方定价页面：

- [OpenAI Pricing](https://openai.com/api/pricing/)
- [Anthropic Pricing](https://www.anthropic.com/pricing)
- [Google AI Pricing](https://ai.google.dev/pricing)
- [Azure OpenAI Pricing](https://azure.microsoft.com/pricing/details/cognitive-services/openai-service/)
- [AWS Bedrock Pricing](https://aws.amazon.com/bedrock/pricing/)
- [DeepSeek Pricing](https://platform.deepseek.com/api-docs/pricing)
- [Cohere Pricing](https://cohere.com/pricing)
- [Mistral Pricing](https://mistral.ai/pricing/)

## 部署到 GitHub Pages

### 方法一：通过 GitHub 网页界面（推荐新手）

1. **创建 GitHub 仓库**
   - 访问 [github.com](https://github.com) 并登录
   - 点击右上角 `+` → `New repository`
   - 仓库名称填写 `MegaToken`
   - 选择 `Public`（公开）
   - 点击 `Create repository`

2. **上传代码**
   - 在仓库页面点击 `uploading an existing file`
   - 拖拽或选择您本地的所有项目文件
   - 点击 `Commit changes`

3. **启用 GitHub Pages**
   - 进入仓库 → `Settings` → `Pages`
   - `Source` 选择 `GitHub Actions`
   - 系统会自动识别 `.github/workflows/update.yml`

4. **完成**
   - 等待几分钟，访问 `https://您的用户名.github.io/MegaToken/`

### 方法二：通过命令行（推荐开发者）

1. **安装 Git**
   - 下载并安装 [Git for Windows](https://git-scm.com/download/win)

2. **初始化仓库并推送**
   ```bash
   cd MegaToken
   git init
   git add .
   git commit -m "Initial commit"
   git branch -M main
   git remote add origin https://github.com/您的用户名/MegaToken.git
   git push -u origin main
   ```

3. **启用 GitHub Pages**
   - 进入 GitHub 仓库 → `Settings` → `Pages`
   - `Source` 选择 `GitHub Actions`

### 方法三：通过 GitHub Desktop（图形界面）

1. **下载 GitHub Desktop**
   - 访问 [desktop.github.com](https://desktop.github.com) 下载

2. **添加本地仓库**
   - 打开 GitHub Desktop → `File` → `Add local repository`
   - 选择您的 `MegaToken` 文件夹

3. **发布到 GitHub**
   - 点击 `Publish repository`
   - 填写仓库名称 `MegaToken`
   - 选择 `Keep this code private`（取消勾选，保持公开）
   - 点击 `Publish Repository`

4. **启用 GitHub Pages**
   - 进入 GitHub 仓库网页 → `Settings` → `Pages`
   - `Source` 选择 `GitHub Actions`

## 自动更新配置

项目已配置 GitHub Actions，会自动：

- **每周一凌晨**自动抓取最新价格
- **推送到 main 分支时**自动重新部署
- **手动触发**：进入 Actions 页面点击 `Run workflow`

## 自定义域名（可选）

1. 在仓库根目录创建 `CNAME` 文件
2. 文件内容填写您的域名，如 `prices.yourdomain.com`
3. 在域名 DNS 设置中添加 CNAME 记录指向 `您的用户名.github.io`

## 贡献

欢迎通过以下方式贡献：

- 提交 Issue 报告价格变动
- 提交 PR 改进代码
- 补充更多厂商的价格数据

## 免责声明

- 数据源自公开定价页面，仅供参考
- 实际价格请以各厂商官方为准
- 本项目为非营利性质，不代表任何厂商立场

## License

MIT License