---
name: dev-collab-ultimate-v5
description: 活跃版 v5 — dev-collab-auto + dual-remote-git + dev-pipeline-auto 三合一，门控去重+严格步进+dev-log
version: 5.0.0
---

# Dev Collab Ultimate v5.0.0 — 门控去重 + 步进依赖锁

> 从 v4.4.0 冻结版复制，v5 新增四大能力

## v5 新增能力概览

| 能力 | 模块 | 说明 |
|------|------|------|
| **动态分配** | `pipeline-analyzer.py` | 分析方案自动判断难度(1-3)，动态分配 V4-Flash/Pro 模型 |
| **视觉验证** | `pipeline-vision-check.py` | 需要时调用 OpenClaw+Kimi 截图验证界面渲染 |
| **修复回环** | `pipeline-fix-loop.py` | pytest 失败自动调用 Claude Code 修复，最多 3 轮 |
| **三级同步** | workspace + dev-log + git | 任务传递 + 状态追踪 + 持久化 |

### 动态难度分配

```
方案分析 → pipeline-analyzer.py:
  ├─ 难度1(简单): <5功能点, 单模块 → 编码:Flash, 测试:Flash
  ├─ 难度2(中等): 5-10功能点, 2-3模块 → 编码:Flash, 测试:Pro
  └─ 难度3(困难): >10功能点, GUI/复杂算法 → 编码:Pro, 测试:Pro

视觉验证: 检测方案关键词(GUI/Web/界面/curses等) → 自动启用
```

### 自动修复回环

```
Tab2 pytest 失败
    ↓
pipeline-fix-loop.py 捕获错误 → 提取失败测试 + 错误行号
    ↓
调用 Claude Code 修复（传入错误上下文）
    ↓
重新 pytest → 如果仍有失败 → 最多 3 轮
    ↓
全部通过 → 归档 | 3轮未过 → 停止 + dev-log 记录
```

### 视觉验证（按需启用）

```
config.json need_vision=true
    ↓
tab2 自动调用 pipeline-vision-check.py:
  ├─ 启动目标程序
  ├─ OpenClaw 截图
  ├─ Kimi 视觉分析界面渲染
  └─ 输出验证结果
```

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
 │   [门控去重] 检查项目名在开发中/开发完是否存在  │
 │     ├─ 已存在 → ⏭️ 跳过                       │
 │     └─ 不存在 → 🚀 启动开发流程               │
 └───────────────────────────────────────────────┘
```

## 严格步进 9 步（严格执行，不可跳步）

```
步0 ── 门控去重 ── [watchdog自动] 项目名不重复才继续
步1 ── 方案解析 ── [Hermes] 生成 MANIFEST.md
步2 ── 任务拆解 ── [Hermes] 生成 3 个 task.md（含步进锁）
                       ↓
步3 ── 编码 ────── [Tab1 Claude Code] 写全部代码
                   完成后在 claude_task.md 写入 ✅ step_3_done（独占一行）
                       ↓ grep "^✅ step_3_done" 精确匹配
步4 ── 测试 ────── [Tab3 OpenCode] 写 pytest → 全部通过
                   完成后在 opencode_task.md 写入 ✅ step_4_done（独占一行）
                       ↓ grep "^✅ step_4_done" 精确匹配
步5 ── 验证 ────── [Tab2] cd 项目根 → find tests/ → 传相对路径跑 pytest
步6 ── 清理 ────── [Tab2] 删 __pycache__ .pytest_cache
步7 ── 归档 ────── [Tab2] Sandbox/ → 开发完/ + 清理 开发中/
步8 ── 双推 ────── [Tab2] git push GitHub + Gitee
```

**执行顺序保证**：

```
Tab1 启动 → 编码 → 写 ✅ step_3_done
               ↓ grep "^✅ step_3_done"（行开头，不含指令文字）
Tab3 检测到 → 测试 → 写 ✅ step_4_done
               ↓ grep "^✅ step_4_done"（行开头，不含指令文字）
Tab2 检测到 → 等测试文件 → pytest → 清理 → 归档 → 双推
```

**任何一步失败 → dev-log 记录错误 → 停止后续 → 人工排查**

## 3 个 WT 标签行为

### Tab1 — Claude Code（编码）

```
5秒倒计时 → claude -p "读取 .workspace/claude_task.md 按需求写代码"
→ 编码全部完成后，在 claude_task.md 末尾写入 ✅ step_3_done（独占一行）
→ 退出
→ 🔒 Tab3 通过 grep "^✅ step_3_done" 检测到此行后才启动
```

### Tab3 — OpenCode（测试）

```
5秒倒计时
→ 🔒 步进锁: 循环用 grep "^✅ step_3_done" 检查 claude_task.md
  无 → sleep 5 → 再查（最多等 15 分钟）
  有 → 读取 opencode_task.md
      → opencode run —message "写 pytest 测试，全部通过"
      → 测试通过后在 opencode_task.md 写入 ✅ step_4_done（独占一行）
      → 退出
→ 🔒 Tab2 通过 grep "^✅ step_4_done" 检测到此行后才启动
```

### Tab2 — Ultimate（验证+清理+归档+双推）

```
5秒倒计时
→ 🔒 步进锁: 循环用 grep "^✅ step_4_done" 检查 opencode_task.md
  无 → sleep 5 → 再查（最多等 15 分钟）
  有 → find PROJECT_DIR -type d -name tests → 取相对路径
      → 重试: 如果 tests/ 为空，每 5 秒重试（最多 60 秒）
      → python3 -m pytest gomoku/tests/ -v（传路径，不 cd）
      → rm -rf __pycache__ .pytest_cache（清理）
      → cp -a Sandbox/ → 开发完/（归档）
      → rm -rf 开发中/同名目录
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
python3 ~/.hermes/scripts/pipeline_watchdog.py gate 项目名
python3 ~/.hermes/scripts/pipeline_watchdog.py status
```

## 定时任务

| 任务 | 频率 | 脚本 | 作用 |
|------|------|------|------|
| `pipeline-scan` | 每 30 分钟 | pipeline-scan.sh | 门控扫描 |
| `pipeline-sync` | 每天 21:00 | pipeline-sync.sh | 同步到远程 |

## 三重闭环触发

| 闭环 | 机制 | 频率 | 说明 |
|------|------|------|------|
| **[1]** | **cron** `pipeline-scan` | 每 30 分钟 | 系统级永不休眠 |
| **[2]** | **后台守护进程** `pipeline-monitor` | 每 30 分钟 | `.bashrc` 自启 |
| **[3]** | **手动** scan | 随时 | 手动触发 |

## 依赖 Skill

| Skill | 用途 |
|-------|------|
| `dev-collab-auto` | Tab1 Claude Code + Tab3 OpenCode |
| `dual-remote-git` | 双远程仓库 CRUD |
| `dev-pipeline-auto` v2 | 门控调度 + dev-log + 归档 |
