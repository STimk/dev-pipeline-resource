---
name: dev-collab-ultimate-active
description: active — 门控去重+步进锁+dev-log+动态分配+视觉验证+修复回环+三重闭环+thinking修复，10坑全修。固定版本名，后续迭代不更名
version: 1.0.0
---

# Dev Collab Ultimate active — 固定部署版

> 版本名固化，路径不变，直接下载部署

## 能力一览

| 能力 | 说明 |
|------|------|
| 门控去重 | 按项目名检查开发中/开发完，有则跳过 |
| 步进锁 | Tab1→step_3→Tab3→step_4→Tab2 严格串行 |
| dev-log | 12步状态追踪 |
| 动态分配 | pipeline-analyzer.py 自动判断难度分配模型 |
| 视觉验证 | OpenClaw+Kimi 截图分析（按需） |
| 修复回环 | pytest失败→Claude修复→重验最多3轮 |
| 三重闭环 | cron + 守护进程 + 手动触发 |
| thinking修复 | ANTHROPIC_DANGEROUSLY_NO_THINKING=1 |

## 快速部署

```bash
# 1. 克隆资源包
git clone https://github.com/STimk/dev-pipeline-resource.git

# 2. 安装 skill（路径固定）
cp archive/dev-collab-ultimate-active.md ~/.hermes/skills/software-development/dev-collab-ultimate-active/SKILL.md

# 3. 安装脚本
cp scripts/* ~/.hermes/scripts/
chmod +x ~/.hermes/scripts/*.sh

# 4. 安装守护进程
bash ~/.hermes/scripts/setup-pipeline-monitor.sh

# 5. 加载
hermes -s dev-collab-ultimate-active
```

## 流程

```
你写方案 → 待开发/YYYY-MM-DD-项目名/开发方案.md
     │
     ⏰ 三重闭环触发
     ▼
门控去重 + 动态分析(config.json)
     │
Tab1 Claude Code → 编码 → ✅ step_3_done
     ↓ grep "^✅ step_3_done"
Tab3 OpenCode → 测试 → ✅ step_4_done  
     ↓ grep "^✅ step_4_done"
Tab2 Ultimate → 验证+修复回环 → 清理 → 归档 → 双推
```

## 依赖

| Skill | 用途 |
|-------|------|
| `dev-collab-auto` | Tab1 + Tab3 脚本 |
| `dual-remote-git` | 双远程推送 |
| `dev-pipeline-auto` v2 | 门控+dev-log |
