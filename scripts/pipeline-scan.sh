#!/bin/bash
# pipeline-scan.sh v2 — 门控扫描脚本
# 每30分钟由 cron 触发
# 
# 门控逻辑:
#   开发中/ 或 开发完/ 有项目 → 🗑️ 删除待开发/ 全部方案
#   两者都空 → 🚀 自动开发
#
# 日志输出写入 watchdog.log

echo "[$(date '+%Y-%m-%d %H:%M:%S')] Pipeline Scan v2 — 门控扫描启动"
python3 ~/.hermes/scripts/pipeline_watchdog.py scan
echo "[$(date '+%Y-%m-%d %H:%M:%S')] Pipeline Scan v2 — 完成"
