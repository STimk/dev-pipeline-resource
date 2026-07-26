#!/bin/bash
# Tab 1: Claude Code — 全自动编码（步进锁版本）
# 编码完成后在 claude_task.md 追加 "step_3_done"

source ~/.config/opencode/credentials.sh
export ANTHROPIC_BASE_URL="https://api.deepseek.com/anthropic"
export ANTHROPIC_API_KEY="$DEEPSEEK_API_KEY"

cd /mnt/f/AI_Work/Agent/Hermes/Sandbox

echo "============================================="
echo " Claude Code — 编码 (步进锁 v3)"
echo " 5秒后自动执行"
echo "============================================="
echo ""
echo "=== MANIFEST ==="
head -30 .workspace/MANIFEST.md 2>/dev/null
echo ""
echo "=== Claude 任务 ==="
cat .workspace/claude_task.md 2>/dev/null
echo ""
echo "--- 5秒后自动执行 ---"
read -t 5 || true
echo ""
echo "=== 正在执行任务 === "
echo ""

# 执行 Claude Code 编码
/home/zhang/.local/bin/claude -p "
请执行以下步骤：
1. 读取 /mnt/f/AI_Work/Agent/Hermes/Sandbox/.workspace/MANIFEST.md 了解项目上下文
2. 读取 /mnt/f/AI_Work/Agent/Hermes/Sandbox/.workspace/claude_task.md 了解具体任务
3. 执行任务中描述的工作，在项目目录下写全部代码
4. 全部完成后，在 /mnt/f/AI_Work/Agent/Hermes/Sandbox/.workspace/claude_task.md 末尾追加一行: ✅ step_3_done
" --dangerously-skip-permissions --max-turns 30

# 不设兜底标记 — 如果 Claude Code 没写 step_3_done，自动重试最多2次
CLAUDE_RETRIES=0
while ! grep -q "^✅ step_3_done" .workspace/claude_task.md 2>/dev/null; do
    CLAUDE_RETRIES=$((CLAUDE_RETRIES + 1))
    if [ $CLAUDE_RETRIES -gt 2 ]; then
        echo "❌ Claude Code 重试${CLAUDE_RETRIES}次仍未完成"
        break
    fi
    echo "⚠️ Claude Code 退出但未标记完成，重新启动 ($CLAUDE_RETRIES/2)..."
    /home/zhang/.local/bin/claude -p "
请继续完成 claude_task.md 中描述的工作。
部分代码已存在，请检查并完成剩余文件。
全部完成后，在 .workspace/claude_task.md 末尾追加一行: ✅ step_3_done
" --dangerously-skip-permissions --max-turns 20
done

echo ""
echo "✅ 编码完成 — step_3_done"
