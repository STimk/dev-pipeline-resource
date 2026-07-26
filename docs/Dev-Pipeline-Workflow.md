---
title: "Dev Pipeline — 全自动开发流水线"
tags: [pipeline, dev-collab, workflow, automation]
created: 2026-07-26
updated: 2026-07-26
status: active
---

## 调用的 Skill

`dev-collab-ultimate-v4` v4.1.0

## 三重闭环触发

| 闭环 | 机制 | 频率 |
|------|------|------|
| [1] | cron pipeline-scan | 每 30 分钟 |
| [2] | 后台守护进程 pipeline-monitor | 每 30 分钟 |
| [3] | 手动 scan | 随时 |

## 门控去重

待开发方案 → 检查项目名在 开发中/开发完 是否存在 → 有则跳过，无则开发

## 严格步进

1. 门控去重 → 2. 方案解析 → 3. 任务拆解 → 4. 编码(Tab1 Claude Code) → 5. 测试(Tab3 OpenCode) → 6. 验证(Tab2 pytest) → 7. 清理 → 8. 归档 → 9. 双推

## Skill 依赖链

```
dev-collab-ultimate-v4 v4.1.0     ← 整合入口
├─ dev-collab-auto v1             ← Claude Code + OpenCode 脚本
├─ dual-remote-git v1             ← GitHub + Gitee 双远程推送
└─ dev-pipeline-auto v2           ← 门控去重 + dev-log + 目录规范
     └─ pipeline_watchdog.py      ← 扫描/门控/日志
         pipeline-monitor.sh      ← 后台守护进程
         pipeline-auto-workspace.py ← 自动生成 workspace
```

## 实战排查记录

### 消消乐测试发现的 Bug（已修 v4.1.0）

| # | 问题 | 影响 | 修复 |
|---|------|------|------|
| 1 | step 标记预写在模板 | Tab3不等编码完成就启动 | pipeline-auto-workspace.py 改为追加指令 |
| 2 | 项目名不统一 | tab2 归档路径错误 | 直接用目录全名 YYYY-MM-DD-项目名 |
| 3 | 归档后不清理开发中/ | 项目同时在两个目录 | tab2 归档后清理两个位置 |
| 4 | grep 匹配指令文本 | 步进锁提前释放 | 改为 grep "✅ step_X_done" 精确匹配 |

### 五子棋测试发现的 Bug（已修 v4.1.0）

| # | 问题 | 影响 | 修复 |
|---|------|------|------|
| 5 | pytest 在根目录跑找不到子目录测试 | exit=5 0 tests collected | tab2 自动 find tests/ 子目录再跑 |

## 远程电脑接入

教程文档: `远程电脑接入教程.md`（已同步到仓库根目录）

```bash
# 新电脑首次
git clone git@github.com:STimk/dev-pipeline.git
cd dev-pipeline
cat 远程电脑接入教程.md

# 上传方案
mkdir -p "待开发/$(date +%Y-%m-%d)-项目名"
vim "待开发/$(date +%Y-%m-%d)-项目名/开发方案.md"
git add 待开发/ && git commit -m "feat: 新方案" && git push

# 查看结果
git pull && ls 开发完/ && cat .dev-logs/项目名.json
```

## 常用命令

- `pipeline_watchdog.py scan` — 门控扫描
- `pipeline_watchdog.py status` — 流水线总览
- `pipeline_watchdog.py gate 项目名` — 检查项目
- `pipeline_watchdog.py log 项目名` — 开发日志
- `pipeline-monitor.sh start|stop|status` — 守护进程管理

## 参考

- README: https://github.com/STimk/dev-pipeline
- Skill: `dev-collab-ultimate-v4`
- 脚本: ~/.hermes/scripts/ 下 tab*.sh, pipeline_*.py, pipeline-monitor.sh
