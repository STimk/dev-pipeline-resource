#!/bin/bash
# pipeline-monitor.sh — 三重闭环后台监控守护进程
#
# 三重闭环:
#   [1] cron 每30分钟     ← 系统级兜底，永不休眠
#   [2] 本守护进程 30秒轮询 ← 快速响应，自动全流程
#   [3] 手动命令          ← 随时可触发
#
# 生命周期:
#   启动 → 每30分钟检查待开发/
#       → 发现新方案 → 门控去重
#       → 通过 → 自动生成 workspace
#       → 自动启动 3 个 WT 标签
#       → 持续监控完成状态
#       → 完成 → 继续下一轮
#
# 持久化: 可被 nohup / systemd / .bashrc 拉起
# 日志: ~/.hermes/scripts/pipeline-monitor.log

PIDFILE="$HOME/.hermes/scripts/.pipeline-monitor.pid"
LOGFILE="$HOME/.hermes/scripts/pipeline-monitor.log"
WATCHDOG="$HOME/.hermes/scripts/pipeline_watchdog.py"
WORKSPACE_PY="$HOME/.hermes/scripts/pipeline-auto-workspace.py"
SANDBOX="/mnt/f/AI_Work/Agent/Hermes/Sandbox"
PIPELINE="/mnt/f/AI_Work/Agent/Hermes/Sandbox/dev-pipeline"
WATCH_DIR="$PIPELINE/待开发"

WINDOWS_USER="zhang"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" >> "$LOGFILE"
    echo "$*"
}

start_monitor() {
    if [ -f "$PIDFILE" ]; then
        OLD_PID=$(cat "$PIDFILE")
        if kill -0 "$OLD_PID" 2>/dev/null; then
            log "⚠️ 监控进程已在运行 (PID $OLD_PID)"
            exit 0
        fi
        rm -f "$PIDFILE"
    fi
    
    # 写入 PID
    echo $$ > "$PIDFILE"
    log "🟢 [闭环1] 后台监控启动 (PID $$)"
    log "   扫描间隔: 30分钟"
    log "   日志文件: $LOGFILE"
    
    # 忽略 SIGHUP — 终端关闭也不退出
    trap '' HUP
    
    # 上次已触发的项目（避免重复触发）
    TRIGGERED_FILE="$HOME/.hermes/scripts/.pipeline-triggered.txt"
    touch "$TRIGGERED_FILE"
    
    SCAN_COUNT=0
    
    while true; do
        SCAN_COUNT=$((SCAN_COUNT + 1))
        
        # ── 第1层: 检查待开发/ 是否有新方案 ──
        PLAN_COUNT=$(find "$WATCH_DIR" -name "*.md" -type f 2>/dev/null | wc -l)
        
        if [ "$PLAN_COUNT" -gt 0 ]; then
            # ── 第2层: 运行门控扫描 ──
            SCAN_OUTPUT=$(python3 "$WATCHDOG" scan 2>&1)
            log "🔍 [扫描#$SCAN_COUNT] 发现 $PLAN_COUNT 个方案"
            
            # 检查是否有新项目进入开发中/
            NEW_PROJECT=$(find "$PIPELINE/开发中" -mindepth 1 -maxdepth 1 -type d 2>/dev/null | head -1)
            
            if [ -n "$NEW_PROJECT" ]; then
                PROJECT_NAME=$(basename "$NEW_PROJECT")
                
                # 检查是否已触发过（去重）
                if ! grep -q "^$PROJECT_NAME$" "$TRIGGERED_FILE" 2>/dev/null; then
                    echo "$PROJECT_NAME" >> "$TRIGGERED_FILE"
                    log "🚀 [闭环2] 新项目门控通过: $PROJECT_NAME"
                    
                    # ── 第3层: 自动生成 workspace ──
                    PLAN_FILE=$(find "$WATCH_DIR" -path "*$PROJECT_NAME*" -name "*.md" 2>/dev/null | head -1)
                    if [ -n "$PLAN_FILE" ]; then
                        log "   📋 自动生成 workspace..."
                        python3 "$WORKSPACE_PY" "$PLAN_FILE" 2>&1 | while read line; do log "   $line"; done
                        
                        # ── 第4层: 启动 WT 标签（全自动三联动）──
                        log "   🪟 启动 3 个 WT 标签..."
                        
                        # Tab1: Claude Code
                        powershell.exe -Command "Start-Process -FilePath 'C:\Users\$WINDOWS_USER\AppData\Local\Microsoft\WindowsApps\wt.exe' -ArgumentList '-w 0 nt -d . wsl -d Ubuntu-20.04 -u zhang --cd /home/zhang -e bash -c \"bash ~/.hermes/scripts/tab1-auto.sh\"'" &
                        sleep 3
                        
                        # Tab3: OpenCode
                        powershell.exe -Command "Start-Process -FilePath 'C:\Users\$WINDOWS_USER\AppData\Local\Microsoft\WindowsApps\wt.exe' -ArgumentList '-w 0 nt -d . wsl -d Ubuntu-20.04 -u zhang --cd /home/zhang -e bash -c \"bash ~/.hermes/scripts/tab3-auto.sh\"'" &
                        sleep 3
                        
                        # Tab2: Ultimate
                        powershell.exe -Command "Start-Process -FilePath 'C:\Users\$WINDOWS_USER\AppData\Local\Microsoft\WindowsApps\wt.exe' -ArgumentList '-w 0 nt -d . wsl -d Ubuntu-20.04 -u zhang --cd /home/zhang -e bash -c \"bash ~/.hermes/scripts/tab2-ultimate.sh\"'" &
                        
                        log "   ✅ 3 个 WT 标签已启动，实时可见"
                        log "   📍 Tab1: Claude Code (编码)"
                        log "   📍 Tab3: OpenCode (测试，等编码完成)"
                        log "   📍 Tab2: Ultimate (验证→归档→双推，等测试完成)"
                    fi
                fi
            fi
        fi
        
        # 每 300 次扫描清一次 triggered 列表（防止无限堆积）
        if [ $((SCAN_COUNT % 300)) -eq 0 ]; then
            # 只保留仍在开发中/ 的项目
            > "$TRIGGERED_FILE"
            for d in "$PIPELINE/开发中"/*/; do
                [ -d "$d" ] && basename "$d" >> "$TRIGGERED_FILE"
            done
            log "🧹 清理 triggered 列表"
        fi
        
        sleep 1800  # 30分钟
    done
}

stop_monitor() {
    if [ -f "$PIDFILE" ]; then
        PID=$(cat "$PIDFILE")
        if kill -0 "$PID" 2>/dev/null; then
            kill "$PID" 2>/dev/null
            log "🔴 监控进程已停止 (PID $PID)"
        fi
        rm -f "$PIDFILE"
    else
        log "⚠️ 没有运行中的监控进程"
    fi
}

status_monitor() {
    if [ -f "$PIDFILE" ]; then
        PID=$(cat "$PIDFILE")
        if kill -0 "$PID" 2>/dev/null; then
            echo "🟢 监控进程运行中 (PID $PID)"
            echo "   日志: $LOGFILE"
            echo "   启动时间: $(ps -o lstart= -p $PID 2>/dev/null)"
            echo ""
            echo "=== 最近 10 条日志 ==="
            tail -10 "$LOGFILE" 2>/dev/null
        else
            echo "🔴 PID 文件存在但进程已死"
            rm -f "$PIDFILE"
        fi
    else
        echo "🔴 监控进程未运行"
    fi
}

case "${1:-status}" in
    start)
        start_monitor
        ;;
    stop)
        stop_monitor
        ;;
    restart)
        stop_monitor
        sleep 1
        start_monitor
        ;;
    status)
        status_monitor
        ;;
    *)
        echo "用法: $0 {start|stop|restart|status}"
        echo ""
        echo "三重闭环监控系统"
        echo "  [1] cron 每30分钟 — 系统级兜底"
        echo "  [2] 本守护进程     — 30秒快速响应"
        echo "  [3] 手动命令       — 随时触发"
        exit 1
        ;;
esac
