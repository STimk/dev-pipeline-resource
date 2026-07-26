---
name: dev-collab-ultimate
description: 初代版 — dev-collab-auto + dual-remote-git + dev-pipeline-auto 三合一，门控去重+严格步进+dev-log
version: 3.0.0
---

# Dev Collab Ultimate v3 — 门控去重 + 步进依赖锁

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
     ⏰ cron 每30分钟
     ▼
 ┌─ pipeline_watchdog.py scan ──────────────────┐
 │   [门控去重] 检查项目名在开发中/开发完是否存在  │
 │     ├─ 已存在 → ⏭️ 跳过                       │
 │     └─ 不存在 → 🚀 启动开发流程               │
 └───────────────────────────────────────────────┘
```

## 严格步进 9 步

```
步0 ── 门控去重 ── [watchdog自动] 项目名不重复才继续
步1 ── 方案解析 ── [Hermes] 生成 MANIFEST.md
步2 ── 任务拆解 ── [Hermes] 生成 3 个 task.md（含步进锁）
步3 ── 编码 ────── [Tab1 Claude Code] 写全部代码
步4 ── 测试 ────── [Tab3 OpenCode] 写 pytest → 跑测试
                    依赖: 等步3完成 (step_3_done)
步5 ── 验证 ────── [Tab2] pytest 全部通过
                    依赖: 等步4完成 (step_4_done)
步6 ── 清理 ────── [Tab2] 删 __pycache__ .pytest_cache
步7 ── 归档 ────── [Tab2] 开发中/ → 开发完/
步8 ── 双推 ────── [Tab2] git push GitHub + Gitee
```

**任何一步失败 → dev-log 记录错误 → 停止后续 → 人工排查**

## 3 个 WT 标签行为

### Tab1 — Claude Code（编码）

```
5秒倒计时 → claude -p "读取 .workspace/claude_task.md 按需求写代码"
→ 编码完成后在 claude_task.md 追加 "✅ step_3_done"
→ 退出
```

### Tab3 — OpenCode（测试）

```
5秒倒计时
→ 循环检查 claude_task.md 是否有 "step_3_done"
  无 → sleep 5 → 再查（最多等 5 分钟）
  有 → 读取 opencode_task.md
      → opencode run —message "写 pytest 测试，全部通过"
      → 测试通过后在 opencode_task.md 追加 "✅ step_4_done"
      → 退出
```

### Tab2 — Ultimate（验证+清理+归档+双推）

```
5秒倒计时
→ 循环检查 opencode_task.md 是否有 "step_4_done"
  无 → sleep 5 → 再查（最多等 5 分钟）
  有 → 读取 MANIFEST.md 获取 PROJECT_NAME
      → cd PROJECT_DIR
      → pytest -v（验证）
      → rm -rf __pycache__ .pytest_cache *.pyc（清理）
      → cp -a 开发中/→开发完/（归档）
      → git add + commit + push（双推）
      → update dev-log step 5-8 done
      → 退出
```

## 启动命令

```powershell
# Tab1: Claude Code
powershell.exe -Command "Start-Process -FilePath 'C:\Users\zhang\AppData\Local\Microsoft\WindowsApps\wt.exe' -ArgumentList '-w 0 nt -d . wsl -d Ubuntu-20.04 -u zhang --cd /home/zhang -e bash -c \"bash ~/.hermes/scripts/tab1-auto.sh\"'"
# Tab2: Ultimate
powershell.exe -Command "Start-Process -FilePath 'C:\Users\zhang\AppData\Local\Microsoft\WindowsApps\wt.exe' -ArgumentList '-w 0 nt -d . wsl -d Ubuntu-20.04 -u zhang --cd /home/zhang -e bash -c \"bash ~/.hermes/scripts/tab2-ultimate.sh\"'"
# Tab3: OpenCode
powershell.exe -Command "Start-Process -FilePath 'C:\Users\zhang\AppData\Local\Microsoft\WindowsApps\wt.exe' -ArgumentList '-w 0 nt -d . wsl -d Ubuntu-20.04 -u zhang --cd /home/zhang -e bash -c \"bash ~/.hermes/scripts/tab3-auto.sh\"'"
```

## dev-log 查看

```bash
python3 ~/.hermes/scripts/pipeline_watchdog.py log 2026-07-26-项目名
python3 ~/.hermes/scripts/pipeline_watchdog.py gate 项目名   # 检查是否已存在
python3 ~/.hermes/scripts/pipeline_watchdog.py status        # 流水线总览
```

## 定时任务

| 任务 | 频率 | 脚本 | 作用 |
|------|------|------|------|
| `pipeline-scan` | 每 30 分钟 | pipeline-scan.sh | 门控扫描：检测待开发/ → 按项目名去重 → 跳过或开发 |
| `pipeline-sync` | 每天 21:00 | pipeline-sync.sh | 同步到远程 |

## 依赖 Skill

| Skill | 用途 |
|-------|------|
| `dev-collab-auto` | Tab1 Claude Code + Tab3 OpenCode |
| `dual-remote-git` | 双远程仓库 CRUD |
| `dev-pipeline-auto` v2 | 门控调度 + dev-log + 归档 |
