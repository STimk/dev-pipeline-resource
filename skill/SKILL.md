---
name: dev-collab-ultimate-v4
description: 稳定版 v4 — dev-collab-auto + dual-remote-git + dev-pipeline-auto 三合一，门控去重+严格步进+dev-log
version: 4.4.0

# Dev Collab Ultimate v4.4.0 — 门控去重 + 步进依赖锁

> 从 v4.2.3 迭代，持续修复实战发现的问题

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
python3 ~/.hermes/scripts/pipeline_watchdog.py gate 项目名   # 检查是否已存在
python3 ~/.hermes/scripts/pipeline_watchdog.py status        # 流水线总览
```

## 定时任务

| 任务 | 频率 | 脚本 | 作用 |
|------|------|------|------|
| `pipeline-scan` | 每 30 分钟 | pipeline-scan.sh | 门控扫描：检测待开发/ → 按项目名去重 → 跳过或开发 |
| `pipeline-sync` | 每天 21:00 | pipeline-sync.sh | 同步到远程 |

## 三重闭环触发

| 闭环 | 机制 | 频率 | 说明 |
|------|------|------|------|
| **[1]** | **cron** `pipeline-scan` | 每 30 分钟 | 系统级永不休眠 |
| **[2]** | **后台守护进程** `pipeline-monitor` | 每 30 分钟 | `.bashrc` 自启，自动生成 workspace + 启动 WT 标签 |
| **[3]** | **手动** scan | 随时 | 手动触发 |

守护进程管理：
```bash
bash ~/.hermes/scripts/pipeline-monitor.sh start|stop|status
bash ~/.hermes/scripts/setup-pipeline-monitor.sh  # 安装
```

## 已知坑（从实战排查）

### 1. step 标记不能预写在模板
```
❌ 问题: workspace 模板里预写了 "✅ step_3_done"
   结果: Tab3 立即检测到标记，不等编码完成就启动
✅ 修复: 模板只写"追加标记"的指令，不写标记本身
   tab 脚本有兜底: 如果 agent 没追加，脚本自动补
```

### 2. 项目名必须统一
```
❌ 问题: watchdog 用 "2026-07-26-项目名"，workspace 提取 "项目名"
   结果: tab2 归档路径错误，找不到项目目录
✅ 修复: pipeline-auto-workspace.py 直接用目录全名
   tab2 同时检查 Sandbox/ 和 开发中/ 两个位置
```

### 3. 归档后必须清理开发中/
```
❌ 问题: tab2 只删 Sandbox/，不删 开发中/
   结果: 项目同时出现在 开发中/ 和 开发完/
✅ 修复: tab2-ultimate.sh 归档后清理 开发中/ 同名目录
```

### 4. 步进锁要求严格的 grep 锚定
```
❌ 问题: grep "✅ step_3_done" 匹配到指令文字 "追加一行: ✅ step_3_done"
   结果: 步进锁形同虚设，3 个 tab 实际上是并发执行
✅ 修复: grep "^✅ step_3_done" 行开头锚定，只匹配独立标记行
   workspace 模板指令改为"标记内容是 ✅" 避免字串匹配
   同时删除所有兜底 fallback，杜绝假标记
```

> 这是最关键的修复。之前 3 个 tab 可以"同时启动"是因为锁根本没锁住。
> 现在必须严格按 Tab1→Tab3→Tab2 顺序执行，下游等上游写入标记。

### 5. WT 标签由 Hermes 自动启动
```
Hermes 用 powershell.exe Start-Process 启动 3 个标签
用户不需要手动操作，看到窗口弹出即可
```

### 6. pytest 找不到测试目录
```
❌ 问题: 代码在子目录 gomoku/ 下，pyproject.toml 在根目录设 testpaths=["tests"]
   结果: cd gomoku/ 后 pytest 仍找到父目录 pyproject.toml，路径错误
✅ 修复: 不 cd 进子目录，而是 find tests/ 后传相对路径给 pytest
   python3 -m pytest gomoku/tests/ -v
```

### 7. 兜底标记导致 step 锁失效
```
❌ 问题: tab1/tab3 的 fallback 在 agent 退出后无脑写 step 标记
   结果: 即使 agent 失败也写假标记，tab2 提前启动，0 tests
✅ 修复: 删除所有兜底 fallback，让三个 tab 的步进锁严格等待
   如果上游真失败，下游最多等 15 分钟后超时报错
```

### 8. TOCTOU: step 标记写入先于测试文件就绪
```
❌ 问题: OpenCode 写 step_4_done 时测试文件还在写入中
   结果: tab2 立即检测到标记，find tests/ 为空，pytest 0 items
✅ 修复: tab2 添加重试循环，发现 tests/ 不存在或为空时
   每 5 秒重试一次，最多等 60 秒
```

### 9. grep 匹配指令文字（即使加了 ✅）
```
❌ 问题: 指令"追加一行: ✅ step_4_done" 包含 "✅ step_4_done"
   结果: grep "✅ step_4_done" 匹配到指令行，不等实际标记
✅ 修复: grep "^✅ step_4_done" 用行开头锚定，只匹配独立标记行
   同时 workspace 模板指令改为"标记内容是 ✅ step_N_done"
   避免指令文字包含可 grep 到的字串
```

## 依赖 Skill

| Skill | 用途 |
|-------|------|
| `dev-collab-auto` | Tab1 Claude Code + Tab3 OpenCode |
| `dual-remote-git` | 双远程仓库 CRUD |
| `dev-pipeline-auto` v2 | 门控调度 + dev-log + 归档 |
