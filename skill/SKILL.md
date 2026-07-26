---
name: dev-collab-ultimate-v6
description: active v6.0.0 — 门控去重+步进锁+dev-log+动态分配+视觉验证+修复回环+三重闭环+thinking修复，10坑全修。版本名固定，后续迭代不更名
version: 6.0.0
---

# Dev Collab Ultimate v6.0.0 — 门控去重 + 步进依赖锁 + 动态分配

> 从 v5.0.0 冻结版复制，后续在此版本上修改

## v6 新增能力（待开发）

| 能力 | 状态 | 说明 |
|------|------|------|
| 动态分配 | ✅ 从 v5 继承 | 难度分析+模型选择+视觉判断 |
| 视觉验证 | ✅ 从 v5 继承 | OpenClaw+Kimi 截图分析 |
| 修复回环 | ✅ 从 v5 继承 | pytest失败→Claude修复→重验 |
| 三级同步 | ✅ 从 v5 继承 | workspace+dev-log+git |

## 概述

| 组件 | 来源 | 功能 |
|------|------|------|
| 门控去重 | `dev-pipeline-auto` v2 | 待开发方案按项目名检查开发中/开发完，有则跳过 |
| 自动开发 | `dev-collab-auto` | WT 标签 Tab1 Cluade Code + Tab3 OpenCode |
| 归档双推 | 本 skill | Tab2 验证→清理→归档→双推 |
| 步进锁 | 本 skill | 每个 task.md 记录 step_N_done，下游等待上游完成 |

## 完整流程

```
你写方案 → 待开发/YYYY-MM-DD-项目名/开发方案.md
     │
     ⏰ 三重闭环触发 [cron/守护进程/手动]
     ▼
 ┌─ pipeline_watchdog.py scan ──────────────────┐
 │   [门控去重] + [动态分析: 难度/模型/视觉]     │
 │     ├─ 项目已存在 → ⏭️ 跳过                   │
 │     └─ 新项目 → 🚀 启动开发流程               │
 └───────────────────────────────────────────────┘
```

## 严格步进 9 步

```
步0 ── 门控去重 ── [watchdog] + 动态分析 config.json
步1 ── 方案解析 ── [Hermes] MANIFEST.md
步2 ── 任务拆解 ── [Hermes] 3 task.md
                       ↓
步3 ── 编码 ────── [Tab1 Claude Code] → ✅ step_3_done
                       ↓ grep "^✅ step_3_done"
步4 ── 测试 ────── [Tab3 OpenCode] → ✅ step_4_done
                       ↓ grep "^✅ step_4_done"
步5 ── 验证+回环 ─ [Tab2] pytest → 失败→fix-loop→最多3轮
步6 ── 清理 ────── [Tab2] rm __pycache__
步7 ── 归档 ────── [Tab2] Sandbox/ → 开发完/ + 清理 开发中/
步8 ── 双推 ────── [Tab2] git push GitHub + Gitee
```

## 10 个已知坑（从 v5 继承）

详见 archive 或资源包 docs。

## 依赖 Skill

| Skill | 用途 |
|-------|------|
| `dev-collab-auto` | Tab1 Claude Code + Tab3 OpenCode |
| `dual-remote-git` | 双远程仓库 CRUD |
| `dev-pipeline-auto` v2 | 门控调度 + dev-log + 归档 |
