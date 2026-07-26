# Dev Pipeline 资源包

> 全自动多 Agent 协作开发流水线 — 门控去重 + 严格步进 + dev-log 追踪
> 稳定版 v4.4.0

## 概述

本资源包包含 `dev-collab-ultimate-v4 v4.4.0` 的全部依赖文件和完整文档。
实现从"写方案"到"自动开发→测试→归档→双推"的全流程自动化。

### 核心能力

```
你写方案 → 待开发/
    ↓ 三重闭环触发 [cron/守护进程/手动]
门控去重 → 检查项目名是否已存在
    ↓ 全新项目
Hermes 生成 workspace → 启动 3 个 WT 标签
    ↓ 步进锁严格串行
Tab1 Claude Code → 编码 → ✅ step_3_done
    ↓ grep "^✅ step_3_done"
Tab3 OpenCode → 测试 → ✅ step_4_done
    ↓ grep "^✅ step_4_done"
Tab2 Ultimate → 验证 → 清理 → 归档 → 双推
```

## 目录结构

```
dev-pipeline-resource/
├── skill/
│   └── SKILL.md                    # dev-collab-ultimate-v4 v4.4.0
├── scripts/
│   ├── tab1-auto.sh                # Tab1 Claude Code 编码 + 步进锁
│   ├── tab2-ultimate.sh            # Tab2 验证→清理→归档→双推
│   ├── tab3-auto.sh                # Tab3 OpenCode 测试 + 步进锁
│   ├── pipeline_watchdog.py        # 门控去重 + dev-log 系统
│   ├── pipeline-auto-workspace.py  # 自动从方案生成 workspace
│   ├── pipeline-monitor.sh         # 后台守护进程（三重闭环[2]）
│   ├── setup-pipeline-monitor.sh   # 一键安装 + .bashrc自启
│   ├── pipeline-scan.sh            # cron 扫描脚本
│   └── pipeline-sync.sh            # cron 同步脚本
└── docs/
    ├── Dev-Pipeline-Workflow.md    # 完整工作流说明
    └── 远程电脑接入教程.md          # 新电脑配置教程
```

## 安装

### 前提条件

| 组件 | 说明 |
|------|------|
| Hermes Agent | AI 代理框架 |
| Claude Code | 编码 Agent（DeepSeek 后端） |
| OpenCode | 测试 Agent（DeepSeek V4-Pro） |
| Windows Terminal | WT 标签页（3 个标签） |
| Python 3.12+ | 脚本运行环境 |
| Git | 版本控制 + 双远程推送 |

### 步骤 1：安装 Skill

```bash
# 将 skill/SKILL.md 复制到 Hermes skills 目录
cp skill/SKILL.md ~/.hermes/skills/software-development/dev-collab-ultimate-v4/

# 验证
hermes -s dev-collab-ultimate-v5
```

### 步骤 2：安装脚本

```bash
# 复制所有脚本到 ~/.hermes/scripts/
cp scripts/* ~/.hermes/scripts/
chmod +x ~/.hermes/scripts/*.sh

# 安装守护进程（自启）
bash ~/.hermes/scripts/setup-pipeline-monitor.sh
```

### 步骤 3：配置流水线仓库

```bash
# 创建流水线仓库
mkdir -p ~/dev-pipeline/{待开发,开发中,开发完}
cd ~/dev-pipeline
git init
git remote add origin git@github.com:STimk/dev-pipeline.git
git remote set-url --add origin git@gitee.com:stimker/dev-pipeline.git
```

## 工作流

### 1. 写方案

```bash
mkdir -p "待开发/$(date +%Y-%m-%d)-项目名称"
vim "待开发/$(date +%Y-%m-%d)-项目名称/开发方案.md"
```

方案格式：

```markdown
# 开发方案：项目名称

## 项目概述
一句话描述。

## 功能需求
1. 功能一
2. 功能二

## 技术栈
- Python 3.12
- 依赖库
```

### 2. 自动触发（三重闭环）

| 闭环 | 机制 | 响应时间 |
|------|------|---------|
| [1] cron | `pipeline-scan` 每 30 分钟 | 最长 30 分钟 |
| [2] 守护进程 | `pipeline-monitor` 每 30 分钟 | 最长 30 分钟 |
| [3] 手动 | `pipeline_watchdog.py scan` | 立即 |

### 3. 自动开发

门控通过后自动执行：

```
步0 ── 门控去重        [watchdog]
步1 ── 方案解析        [Hermes] 生成 MANIFEST.md
步2 ── 任务拆解        [Hermes] 生成 task.md
                       ↓
步3 ── 编码            [Tab1 Claude Code] → ✅ step_3_done
                       ↓ grep "^✅ step_3_done"
步4 ── 测试            [Tab3 OpenCode] → ✅ step_4_done
                       ↓ grep "^✅ step_4_done"
步5 ── 验证            [Tab2] pytest
步6 ── 清理            [Tab2] rm __pycache__
步7 ── 归档            [Tab2] 开发中/ → 开发完/
步8 ── 双推            [Tab2] git push GitHub + Gitee
```

### 4. 查看结果

```bash
# 流水线总览
python3 ~/.hermes/scripts/pipeline_watchdog.py status

# 查看某个项目是否已开发过
python3 ~/.hermes/scripts/pipeline_watchdog.py gate 2026-07-26-项目名

# 查看开发日志
python3 ~/.hermes/scripts/pipeline_watchdog.py log 2026-07-26-项目名
```

## 命令速查

```bash
# 门控扫描
python3 ~/.hermes/scripts/pipeline_watchdog.py scan

# 流水线状态
python3 ~/.hermes/scripts/pipeline_watchdog.py status

# 检查项目是否已存在
python3 ~/.hermes/scripts/pipeline_watchdog.py gate 项目名

# 开发日志
python3 ~/.hermes/scripts/pipeline_watchdog.py log 项目名

# 守护进程管理
bash ~/.hermes/scripts/pipeline-monitor.sh start|stop|status

# 强制开发（跳过门控）
python3 ~/.hermes/scripts/pipeline_watchdog.py force
```

## 已知坑（已修复）

| # | 问题 | 修复 |
|---|------|------|
| 1 | step 标记预写在模板 → Tab3 不等编码完成 | 改为追加模式 |
| 2 | 项目名不统一 → 归档路径错误 | 直接用目录全名 |
| 3 | 归档后不清理开发中/ → 项目在两处 | tab2 清理两处 |
| 4 | grep `"step_3_done"` 匹配指令文字 → 锁提前释放 | 改为 `grep "^✅ step_3_done"` 行开头锚定 |
| 5 | pytest 在根目录跑找不到 `gomoku/tests/` | 传相对路径 |
| 6 | 兜底 fallback 无脑写 step 标记 → 0 tests | 删除所有 fallback |
| 7 | TOCTOU: step 标记写入先于测试文件就绪 | 重试 12 次 × 5 秒 |
| 8 | grep 匹配指令文字（即使加了 ✅） | `^` 锚定 + 指令不写标记原文 |

## 版本历史

| 版本 | 路径 | 状态 |
|------|------|------|
| v3.0.0 | `archive/dev-collab-ultimate-v3.0.0.md` | 初代版（冻结） |
| v4.4.0 | `skill/SKILL.md` | **稳定版（当前）** |

> 每次更新版本时，我会把当前稳定版复制到 `archive/` 再更新 `skill/SKILL.md`。
> 需要回退时直接取 `archive/` 里对应版本覆盖 `skill/SKILL.md` 即可。

### 版本回退方法

```bash
# 查看所有归档版本
ls archive/

# 回退到 v3.0.0
cp archive/dev-collab-ultimate-v3.0.0.md skill/SKILL.md

# 重新加载 skill
hermes -s dev-collab-ultimate-v5
```

## 依赖

| 组件 | 用途 |
|------|------|
| `dev-collab-auto` | Tab1 Claude Code + Tab3 OpenCode 脚本 |
| `dual-remote-git` | GitHub + Gitee 双远程推送 |
| `dev-pipeline-auto` v2 | 门控调度 + dev-log + 目录规范 |

## 许可证

MIT
