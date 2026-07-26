# Dev Pipeline 部署指南

> 稳定部署版 v4.4 — 下载即用

## 系统要求

| 组件 | 说明 |
|------|------|
| Hermes Agent | AI 代理框架 |
| Claude Code | 编码 Agent（DeepSeek 后端） |
| OpenCode | 测试 Agent（DeepSeek V4-Pro） |
| Windows Terminal | WT 标签页 |
| Python 3.12+ | 脚本运行环境 |
| Git | 版本控制 |

## 快速部署

```bash
# 1. 克隆资源包
git clone https://github.com/STimk/dev-pipeline-resource.git
cd dev-pipeline-resource

# 2. 安装 skill
cp archive/dev-collab-ultimate-v4.4.md ~/.hermes/skills/software-development/dev-collab-ultimate-v4.4/SKILL.md

# 3. 安装脚本
cp scripts/* ~/.hermes/scripts/
chmod +x ~/.hermes/scripts/*.sh

# 4. 安装守护进程
bash ~/.hermes/scripts/setup-pipeline-monitor.sh

# 5. 创建流水线仓库
mkdir -p ~/dev-pipeline/{待开发,开发中,开发完}
cd ~/dev-pipeline
git init
git remote add origin git@github.com:STimk/dev-pipeline.git
git remote set-url --add origin git@gitee.com:stimker/dev-pipeline.git
```

## 加载

```bash
hermes -s dev-collab-ultimate-v4.4
```

## 文件说明

```
dev-pipeline-resource/
├── skill/SKILL.md          ← 当前活跃版 (v6)
├── archive/
│   ├── dev-collab-ultimate-v3.0.0.md   初代版
│   ├── dev-collab-ultimate-v4.4.0.md   冻结版
│   ├── dev-collab-ultimate-v4.4.md     部署版 ← 下载这个
│   └── dev-collab-ultimate-v5.0.0.md   冻结版
├── scripts/                ← 9 个运行脚本
├── docs/                   ← 说明文档
├── DEPLOY.md               ← 本部署指南
└── README.md               ← 完整说明
```

## 开始使用

```bash
# 写方案
mkdir -p "dev-pipeline/待开发/$(date +%Y-%m-%d)-项目名"
vim "dev-pipeline/待开发/$(date +%Y-%m-%d)-项目名/开发方案.md"

# 触发开发（等待 cron 30分钟 或手动）
python3 ~/.hermes/scripts/pipeline_watchdog.py scan

# 查看状态
python3 ~/.hermes/scripts/pipeline_watchdog.py status
```
