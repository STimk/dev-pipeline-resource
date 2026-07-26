# Dev Pipeline 完整部署指南

> 版本: active（固定版本名，路径不变）
> 下载即用，后续更新只需 git pull

## 环境要求

| 组件 | 版本 | 获取方式 |
|------|------|---------|
| Hermes Agent | 最新 | `pip install hermes-agent` |
| Claude Code | ≥2.1 | `npm install -g @anthropic-ai/claude-code` |
| OpenCode | 最新 | `npm install -g opencode` |
| Python | ≥3.12 | `apt install python3` |
| Git | ≥2.0 | `apt install git` |
| Windows Terminal | 最新 | Microsoft Store |

## 一键部署

```bash
# 1. 下载资源包
git clone https://github.com/STimk/dev-pipeline-resource.git
cd dev-pipeline-resource

# 2. 安装 skill（路径永久固定）
mkdir -p ~/.hermes/skills/software-development/dev-collab-ultimate-active
cp archive/dev-collab-ultimate-active.md ~/.hermes/skills/software-development/dev-collab-ultimate-active/SKILL.md

# 3. 安装脚本
mkdir -p ~/.hermes/scripts
cp scripts/*.sh scripts/*.py ~/.hermes/scripts/
chmod +x ~/.hermes/scripts/*.sh

# 4. 安装守护进程（开机自启）
bash ~/.hermes/scripts/setup-pipeline-monitor.sh

# 5. 创建流水线仓库
mkdir -p ~/dev-pipeline/{待开发,开发中,开发完}
cd ~/dev-pipeline
git init
git remote add origin git@github.com:STimk/dev-pipeline.git
```

## 加载

```bash
hermes -s dev-collab-ultimate-active
```

## 文件说明

```
~/.hermes/
├── skills/software-development/
│   └── dev-collab-ultimate-active/SKILL.md    ← 加载入口
└── scripts/
    ├── tab1-auto.sh            Claude Code 编码
    ├── tab2-ultimate.sh        验证→清理→归档→双推
    ├── tab3-auto.sh            OpenCode 测试
    ├── pipeline_watchdog.py    门控去重 + dev-log
    ├── pipeline-auto-workspace.py 自动生成 workspace
    ├── pipeline-analyzer.py    动态难度分析
    ├── pipeline-fix-loop.py    自动修复回环
    ├── pipeline-vision-check.py OpenClaw+Kimi 视觉验证
    ├── pipeline-monitor.sh     后台守护进程
    └── setup-pipeline-monitor.sh 一键安装自启

~/dev-pipeline/
├── 待开发/    ← 你写开发方案放这里
├── 开发中/    ← 自动生成的代码
└── 开发完/    ← 验证完成的项目
```

## 快速开始

```bash
# 1. 写方案
mkdir -p "~/dev-pipeline/待开发/$(date +%Y-%m-%d)-项目名"
vim "~/dev-pipeline/待开发/$(date +%Y-%m-%d)-项目名/开发方案.md"

# 2. 触发（等待自动检测或手动）
cd ~/dev-pipeline
python3 ~/.hermes/scripts/pipeline_watchdog.py scan

# 3. 查看状态
python3 ~/.hermes/scripts/pipeline_watchdog.py status
```

## 更新

```bash
cd ~/dev-pipeline-resource
git pull
cp archive/dev-collab-ultimate-active.md ~/.hermes/skills/software-development/dev-collab-ultimate-active/SKILL.md
cp scripts/* ~/.hermes/scripts/
echo "✅ 更新完成"
```
