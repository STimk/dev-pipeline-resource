#!/bin/bash
# Tab 3: OpenCode — 全自动测试（步进锁版本）
# 依赖: 等 claude_task.md 出现 "step_3_done" 再开始
# 完成后在 opencode_task.md 追加 "step_4_done"

export PATH="$PATH:/home/zhang/.nvm/versions/node/v24.18.0/bin"
source ~/.config/opencode/credentials.sh
export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"

cd /mnt/f/AI_Work/Agent/Hermes/Sandbox

echo "==============================================="
echo " OpenCode — 测试 (步进锁 v1.1.0)"
echo " 5秒后检查依赖，等编码完成自动开始"
echo "==============================================="
echo ""
echo "=== MANIFEST ==="
head -20 .workspace/MANIFEST.md 2>/dev/null
echo ""
echo "=== OpenCode 任务 ==="
cat .workspace/opencode_task.md 2>/dev/null
echo ""

# ── 步进依赖锁: 等 Tab1 完成编码 ──
echo "--- 等待 step_3_done (编码完成) ---"
MAX_WAIT=900  # 最多等 15 分钟（网络等原因）
WAITED=0
while ! grep -q "^✅ step_3_done" .workspace/claude_task.md 2>/dev/null; do
    if [ $WAITED -ge $MAX_WAIT ]; then
        echo "❌ 等待超时 ($MAX_WAIT 秒) — claude_task.md 未标记完成"
        echo "检查内容:"
        cat .workspace/claude_task.md 2>/dev/null
        exit 1
    fi
    sleep 5
    WAITED=$((WAITED + 5))
    if [ $((WAITED % 30)) -eq 0 ]; then
        echo "   已等待 ${WAITED}s ..."
    fi
done
echo "✅ step_3_done 已检测到 — 编码完成，开始测试"
echo ""

echo "=== 正在执行测试任务 === "
echo ""

# 执行 OpenCode 测试
opencode run --model deepseek/deepseek-v4-pro --variant max "
请执行以下步骤：
1. 读取 /mnt/f/AI_Work/Agent/Hermes/Sandbox/.workspace/MANIFEST.md 了解项目上下文
2. 读取 /mnt/f/AI_Work/Agent/Hermes/Sandbox/.workspace/opencode_task.md 了解具体测试任务
3. 写 pytest 测试并确保全部通过
4. 全部测试通过后，在 /mnt/f/AI_Work/Agent/Hermes/Sandbox/.workspace/opencode_task.md 末尾追加一行: ✅ step_4_done
"
# 不设兜底标记 — 如果 OpenCode 没写 step_4_done，tab2 会等待超时
# 这比写假标记导致提前归档更好

echo ""
echo "✅ 测试完成 — step_4_done"
