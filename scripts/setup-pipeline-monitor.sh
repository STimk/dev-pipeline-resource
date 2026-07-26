#!/bin/bash
# setup-pipeline-monitor.sh — 安装三重闭环监控系统
# 1. 赋予脚本执行权限
# 2. 添加到 .bashrc 实现终端启动时自启
# 3. 立即启动

MONITOR="$HOME/.hermes/scripts/pipeline-monitor.sh"
BASHRC="$HOME/.bashrc"

# 检查语法
bash -n "$MONITOR" || { echo "❌ monitor 语法错误"; exit 1; }

# 添加 .bashrc 自启（如果还没有）
MARKER="# pipeline-monitor auto-start"
if ! grep -q "$MARKER" "$BASHRC" 2>/dev/null; then
    cat >> "$BASHRC" << 'EOF'

# pipeline-monitor auto-start (三重闭环)
if [ -f ~/.hermes/scripts/pipeline-monitor.sh ] && [ -z "$PIPELINE_MONITOR_LOADED" ]; then
    export PIPELINE_MONITOR_LOADED=1
    bash ~/.hermes/scripts/pipeline-monitor.sh status >/dev/null 2>&1
    # 如果没运行就启动
    if ! bash ~/.hermes/scripts/pipeline-monitor.sh status 2>/dev/null | grep -q "运行中"; then
        nohup bash ~/.hermes/scripts/pipeline-monitor.sh start > /dev/null 2>&1 &
    fi
fi
EOF
    echo "✅ 已添加到 .bashrc（终端启动时自动拉起）"
else
    echo "⏭️ .bashrc 已有自启配置"
fi

# 立即启动
bash "$MONITOR" stop 2>/dev/null
sleep 1
nohup bash "$MONITOR" start > /dev/null 2>&1 &

sleep 2
echo ""
bash "$MONITOR" status

echo ""
echo "========================================================"
echo " 三重闭环监控系统已部署"
echo "========================================================"
echo "  [1] cron 每30分钟     ← 系统级"
echo "  [2] 后台守护进程       ← 30分钟轮询 (.bashrc 自启)"
echo "  [3] 手动命令           ← pipeline-monitor.sh start/stop"
echo "========================================================"
echo " 管理命令:"
echo "    bash ~/.hermes/scripts/pipeline-monitor.sh status"
echo "    bash ~/.hermes/scripts/pipeline-monitor.sh stop"
echo "    bash ~/.hermes/scripts/pipeline-monitor.sh start"
echo "========================================================"
