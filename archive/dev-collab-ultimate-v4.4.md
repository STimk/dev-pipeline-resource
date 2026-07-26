---
name: dev-collab-ultimate-v4.4
description: 稳定部署版 v4.4 — dev-collab-auto + dual-remote-git + dev-pipeline-auto 三合一，门控去重+严格步进+dev-log+动态分配+视觉验证+修复回环
version: 4.4.0
---

# Dev Collab Ultimate v4.4 — 稳定部署版

> 基于 v5.0.0 冻结版代码，打包为稳定部署版本

## 能力概览

| 能力 | 模块 | 说明 |
|------|------|------|
| **动态分配** | `pipeline-analyzer.py` | 分析方案自动判断难度(1-3)，动态分配 V4-Flash/Pro 模型 |
| **视觉验证** | `pipeline-vision-check.py` | 需要时调用 OpenClaw+Kimi 截图验证界面渲染 |
| **修复回环** | `pipeline-fix-loop.py` | pytest 失败自动调用 Claude Code 修复，最多 3 轮 |
| **三级同步** | workspace + dev-log + git | 任务传递 + 状态追踪 + 持久化 |

## 完整流程

```
你写方案 → 待开发/YYYY-MM-DD-项目名/开发方案.md
     │
     ⏰ 三重闭环触发 [cron/守护进程/手动]
     ▼
 ┌─ pipeline_watchdog.py scan ──────────────────┐
 │   [门控去重] 检查项目名在开发中/开发完是否存在  │
 │     ├─ 已存在 → ⏭️ 跳过                       │
 │     └─ 不存在 → 🚀 启动开发流程               │
 └───────────────────────────────────────────────┘
```

## 严格步进

```
步0 ── 门控去重 ── [watchdog自动] + 动态分析 config.json
步1 ── 方案解析 ── [Hermes] MANIFEST.md
步2 ── 任务拆解 ── [Hermes] 3 task.md
                       ↓
步3 ── 编码 ────── [Tab1 Claude Code] → ✅ step_3_done
                       ↓ grep "^✅ step_3_done"
步4 ── 测试 ────── [Tab3 OpenCode] → ✅ step_4_done
                       ↓ grep "^✅ step_4_done"
步5 ── 验证+回环 ─ [Tab2] pytest → 失败→fix-loop→最多3轮
步6 ── 清理 ────── [Tab2] rm __pycache__
步7 ── 归档 ────── [Tab2] Sandbox/ → 开发完/
步8 ── 双推 ────── [Tab2] git push GitHub + Gitee
```

## 部署方式

```bash
# 1. 安装 skill
cp SKILL.md ~/.hermes/skills/software-development/dev-collab-ultimate-v4.4/

# 2. 复制脚本
cp scripts/* ~/.hermes/scripts/
chmod +x ~/.hermes/scripts/*.sh

# 3. 安装守护进程
bash ~/.hermes/scripts/setup-pipeline-monitor.sh

# 4. 加载
hermes -s dev-collab-ultimate-v4.4
```

## 依赖

| Skill | 用途 |
|-------|------|
| `dev-collab-auto` | Tab1 Claude Code + Tab3 OpenCode |
| `dual-remote-git` | 双远程仓库 CRUD |
| `dev-pipeline-auto` v2 | 门控调度 + dev-log + 归档 |
