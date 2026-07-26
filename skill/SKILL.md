---
name: dev-collab-ultimate-active
description: active — 门控去重+步进锁+dev-log+动态分配+视觉验证+修复回环+三重闭环+thinking修复，10坑全修。固定版本名，后续迭代不更名
version: 1.1.0
---

# Dev Collab Ultimate active — 固定部署版

> 版本名固化，路径不变，直接下载部署

##  ⚡ 分流决策门（2026-07-26 新增）

启动前自动评估任务规模，选对应模式：

| 改动量 | 模式 | 启动内容 | 适用场景 |
|--------|------|---------|---------|
| 改 1-3 行 / 1 个文件 | **轻量对话** | 无窗口，terminal 直改 + git push | 修 bug、改配置、加日志 |
| 改 2-5 个文件 / 单模块 | **半自动** | 启动 1 个 Tab（Claude Code 编码+测试） | 模块内调优、小功能 |
| 新建功能 / 新项目 / 跨模块 | **全流水线** | 3 个 Tab 自动执行 | 全栈模块、中大型功能 |

> 判断逻辑：评估修改文件数 + 涉及模块数。Hermes 自动选模式，无需你指定。

---

## 能力一览

| 能力 | 说明 |
|------|------|
| 门控去重 | 按项目名检查开发中/开发完，有则跳过 |
| 步进锁 | Tab1→step_3→Tab3→step_4→Tab2 严格串行 |
| dev-log | 12 步状态追踪 |
| 动态分配 | pipeline-analyzer.py 自动判断难度分配模型 |
| 视觉验证 | OpenClaw+Kimi 截图分析（按需启用） |
| 修复回环 | pytest 失败→Claude 修复→重验，最多 3 轮 |
| 三重闭环 | cron + 守护进程 + 手动触发 |
| thinking修复 | `ANTHROPIC_DANGEROUSLY_NO_THINKING=1` |

---

## 严格步进 9 步

```
步 0 — 门控去重            [watchdog] + 动态分析 config.json
步 1 — 方案解析            [Hermes] MANIFEST.md
步 2 — 任务拆解            [Hermes] 3 task.md
                                ↓
步 3 — 编码                [Tab1 Claude Code] → ✅ step_3_done
                                ↓ grep "^✅ step_3_done"
步 3.5 — 测试目录清理（新增） 清理 Sandbox 下旧 __pycache__ / .pytest_cache
                                ↓
步 4 — 测试                [Tab3 OpenCode] → ✅ step_4_done
                                ↓ grep "^✅ step_4_done"
步 5 — 验证 + 修复回环      [Tab2] pytest → 失败→fix-loop→最多 3 轮
步 6 — 清理                [Tab2] rm -rf __pycache__ .pytest_cache
步 7 — 归档                [Tab2] Sandbox/ → 开发完/ + 清理 开发中/
步 8 — 双推                [Tab2] git push origin + gitee
步 9 — 持久化              [Tab2/Hermes] 写 brain 记录
```

### 步 3.5 说明 — 双目录搜索隔离

在步 4 测试执行前，清理 Sandbox 下其他项目的残留缓存，防止 pytest 跑旧 case：

```bash
find Sandbox/ -type d \( -name __pycache__ -o -name .pytest_cache \) -exec rm -rf {} + 2>/dev/null
```

### 步 9 说明 — brain 持久化

每步完成自动写 brain 记录，跨会话可恢复：

```bash
gbrain put "system/dev-pipeline-log/$项目名" \
  --source "自动: dev-collab-ultimate-active" \
  --content "步 $N 完成 at $(date '+%Y-%m-%d %H:%M')"
```

项目启动时检查 brain 恢复断点：

```bash
gbrain query "dev-pipeline-log $项目名"
```

---

## 流程图示

```
你写方案 → 待开发/YYYY-MM-DD-项目名/开发方案.md
     │
     ⏰ 三重闭环触发 [cron/守护进程/手动]
     ▼
分流决策 → 轻量? → 直接对话+git
          → 半自动? → 1 Tab
          → 全流水线? → 继续
     ▼
门控去重 + 动态分析(config.json)
     │
Tab1 Claude Code → 编码 → ✅ step_3_done
     ↓ grep "^✅ step_3_done"
  [清理旧缓存]
     ↓
Tab3 OpenCode → 测试 → ✅ step_4_done
     ↓ grep "^✅ step_4_done"
Tab2 Ultimate → 验证+修复回环 → 清理 → 归档 → 双推 → 写brain
```

---

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

---

## 已知坑与故障恢复

详细文档在 references/ 目录下：

| 文件 | 内容 |
|------|------|
| `references/pitfall-catalog.md` | 12 个已知坑（含 P-11 双目录搜索、P-12 Tab 启动失败） |
| `references/recovery-guide.md` | 6 种故障恢复手册（含 brain 恢复） |

---

## 依赖 Skill

| Skill | 用途 |
|-------|------|
| `dev-collab-auto` | Tab1 + Tab3 脚本 |
| `dual-remote-git` | 双远程推送 |
| `dev-pipeline-auto` v2 | 门控+dev-log |
| `brain-ops` | brain 持久化（可选） |
