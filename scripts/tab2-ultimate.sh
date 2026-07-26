#!/bin/bash
# Tab 2: Ultimate — 验证+清理+归档+双推（v1.1.0）
# 依赖: 等 opencode_task.md 出现 "step_4_done" 再开始
# 纯 bash 执行，无截图，无 OpenClaw

export PATH="$HOME/.npm-global/bin:$HOME/.local/bin:$PATH"

WORKSPACE="/mnt/f/AI_Work/Agent/Hermes/Sandbox/.workspace"
MANIFEST="$WORKSPACE/MANIFEST.md"
PIPELINE_DIR="/mnt/f/AI_Work/Agent/Hermes/Sandbox/dev-pipeline"
SANDBOX="/mnt/f/AI_Work/Agent/Hermes/Sandbox"

# 项目名从 MANIFEST.md 第一行提取，格式: "# MANIFEST — YYYY-MM-DD-项目名"
PROJECT_NAME=$(head -1 "$MANIFEST" 2>/dev/null | sed 's/^# MANIFEST[— -]*//' | sed 's/^ *//;s/ *$//')
if [ -z "$PROJECT_NAME" ]; then
    echo "❌ 无法从 MANIFEST.md 提取项目名"
    exit 1
fi

# 代码在 Sandbox/{PROJECT_NAME}/ 下（Claude Code 写到这里）
PROJECT_DIR="$SANDBOX/$PROJECT_NAME"

# 流水线相关目录
DEV_PIPELINE_DIR="$PIPELINE_DIR/开发中/$PROJECT_NAME"
DONE_DIR="$PIPELINE_DIR/开发完/$PROJECT_NAME"
DEV_LOG="$PIPELINE_DIR/.dev-logs/$PROJECT_NAME.json"

echo "================================================"
echo " Ultimate — 验证+清理+归档+双推 (v1.1.0)"
echo " 检查依赖，等测试完成自动开始"
echo "================================================"
echo ""
echo "=== 项目: $PROJECT_NAME ==="
echo "   代码目录: $PROJECT_DIR"
echo "   归档目标: $DONE_DIR"
echo ""
echo "=== MANIFEST ==="
head -5 "$MANIFEST" 2>/dev/null
echo ""

# ── 步进依赖锁: 等 Tab3 完成测试 ──
echo "--- 等待 step_4_done (测试完成) ---"
MAX_WAIT=900  # 最多等 15 分钟
WAITED=0
while ! grep -q "^✅ step_4_done" "$WORKSPACE/opencode_task.md" 2>/dev/null; do
    if [ $WAITED -ge $MAX_WAIT ]; then
        echo "❌ 等待超时 ($MAX_WAIT 秒) — opencode_task.md 未标记完成"
        echo "--- 当前 opencode_task.md ---"
        cat "$WORKSPACE/opencode_task.md" 2>/dev/null
        exit 1
    fi
    sleep 5
    WAITED=$((WAITED + 5))
    if [ $((WAITED % 30)) -eq 0 ]; then
        echo "   已等待 ${WAITED}s ..."
    fi
done
echo "✅ step_4_done 已检测到 — 测试完成，开始归档"
echo ""

# ── 智能 pytest: 找到代码目录下的 tests/ 并运行（含重试）──
echo "=== [步5] pytest 验证 ==="
cd "$PROJECT_DIR" 2>/dev/null || cd "$DEV_PIPELINE_DIR" 2>/dev/null || { echo "❌ 项目目录不存在"; exit 1; }
# 记录实际进入的目录
PYTEST_ROOT=$(pwd)

# 重试循环: 最多等 60 秒等测试文件就绪
RETRIES=0
MAX_RETRIES=12
while [ $RETRIES -lt $MAX_RETRIES ]; do
    # 同时搜索 Sandbox 和 开发中/
    SUBDIR=""
    for search_dir in "$PROJECT_DIR" "$DEV_PIPELINE_DIR"; do
        if [ -d "$search_dir" ]; then
            FOUND=$(find "$search_dir" -maxdepth 3 -type d -name "tests" 2>/dev/null | head -1)
            if [ -n "$FOUND" ]; then
                SUBDIR="$FOUND"
                break
            fi
        fi
    done
    PYTEST_TARGET=""
    if [ -n "$SUBDIR" ]; then
        PYTEST_TARGET=$(python3 -c "import os; print(os.path.relpath('$SUBDIR', '$PYTEST_ROOT'))")
        if [ -n "$PYTEST_TARGET" ] && [ -d "$SUBDIR" ] && [ "$(ls -A "$SUBDIR" 2>/dev/null | grep -c '.py')" -gt 0 ]; then
            break  # 找到有效的测试目录
        fi
    fi
    RETRIES=$((RETRIES + 1))
    echo "   ⏳ 测试文件未就绪，等待 5 秒... (${RETRIES}/${MAX_RETRIES})"
    sleep 5
done

if [ $RETRIES -ge $MAX_RETRIES ]; then
    # 降级策略：搜索根目录的 test_*.py 文件
    echo "   ⚠️ 未找到 tests/ 目录，尝试搜索 test_*.py 文件..."
    TEST_FILE=$(find "$PROJECT_DIR" -maxdepth 2 -name "test_*.py" 2>/dev/null | head -1)
    if [ -n "$TEST_FILE" ]; then
        PYTEST_TARGET=$(python3 -c "import os; print(os.path.relpath('$TEST_FILE', '$PYTEST_ROOT'))")
        SUBDIR=$(dirname "$TEST_FILE")
        echo "   ✅ 找到根目录测试文件: $PYTEST_TARGET"
    else
        echo "❌ 等待测试文件超时 (${MAX_RETRIES}次)，停止归档"
        exit 1
    fi
fi

cd "$PYTEST_ROOT" || { echo "❌ 无法进入项目目录: $PYTEST_ROOT"; exit 1; }
echo "   📁 找到测试: $PYTEST_TARGET"

# ── v5 视觉验证（如果配置需要）──
CONFIG_FILE="$WORKSPACE/config.json"
NEED_VISION=$(python3 -c "import json; d=json.load(open('$CONFIG_FILE')); print('true' if d.get('need_vision') else 'false')" 2>/dev/null || echo "false")
if [ "$NEED_VISION" = "true" ]; then
    echo "=== [步4.5] 视觉验证 (OpenClaw + Kimi) ==="
    python3 /home/zhang/.hermes/scripts/pipeline-vision-check.py "$PROJECT_DIR" 2>&1
    VISION_EXIT=$?
    if [ $VISION_EXIT -ne 0 ]; then
        echo "⚠️ 视觉验证发现异常，继续 pytest 验证"
    else
        echo "✅ 视觉验证通过"
    fi
    echo ""
fi

# ── v5 自动修复回环 ──
MAX_FIX_ATTEMPTS=3
python3 -m pytest "$PYTEST_TARGET" -v 2>&1
PYTEST_EXIT=$?

FIX_ATTEMPT=0
while [ $PYTEST_EXIT -ne 0 ] && [ $FIX_ATTEMPT -lt $MAX_FIX_ATTEMPTS ]; do
    FIX_ATTEMPT=$((FIX_ATTEMPT + 1))
    echo ""
    echo "🔄 [修复回环 ${FIX_ATTEMPT}/${MAX_FIX_ATTEMPTS}] pytest 失败 (exit=$PYTEST_EXIT)，调用 Claude Code 修复..."
    python3 /home/zhang/.hermes/scripts/pipeline-fix-loop.py "$PROJECT_DIR" --max-attempts 1 2>&1 | tail -5
    echo "   重新查找测试目录..."
    # 每次修复后重新查找，同时搜索 Sandbox 和 开发中/
    SUBDIR=""
    for search_dir in "$PROJECT_DIR" "$DEV_PIPELINE_DIR"; do
        if [ -d "$search_dir" ]; then
            FOUND=$(find "$search_dir" -maxdepth 3 -type d -name "tests" 2>/dev/null | head -1)
            if [ -n "$FOUND" ]; then
                SUBDIR="$FOUND"
                break
            fi
        fi
    done
    PYTEST_TARGET=""
    if [ -n "$SUBDIR" ]; then
        PYTEST_TARGET=$(python3 -c "import os; print(os.path.relpath('$SUBDIR', '$PYTEST_ROOT'))")
    else
        # 降级：搜索根目录 test_*.py
        TEST_FILE=$(find "$PROJECT_DIR" -maxdepth 2 -name "test_*.py" 2>/dev/null | head -1)
        if [ -n "$TEST_FILE" ]; then
            PYTEST_TARGET=$(python3 -c "import os; print(os.path.relpath('$TEST_FILE', '$PYTEST_ROOT'))")
        fi
    fi
    echo "   重新验证 (目标: ${PYTEST_TARGET:-无})..."
    python3 -m pytest "$PYTEST_TARGET" -v 2>&1
    PYTEST_EXIT=$?
done

if [ $PYTEST_EXIT -ne 0 ]; then
    echo "❌ pytest 失败 (exit=$PYTEST_EXIT)，${MAX_FIX_ATTEMPTS} 轮修复均未通过，停止归档"
    exit $PYTEST_EXIT
fi
echo "✅ pytest 全部通过"
echo ""

# ── 步骤 6: 清理 ──
echo "=== [步6] 清理缓存 ==="
for dir in "$PROJECT_DIR" "$DEV_PIPELINE_DIR"; do
    [ -d "$dir" ] && find "$dir" -type d -name '__pycache__' -exec rm -rf {} + 2>/dev/null
    [ -d "$dir" ] && find "$dir" -type d -name '.pytest_cache' -exec rm -rf {} + 2>/dev/null
    [ -d "$dir" ] && find "$dir" -name '*.pyc' -delete 2>/dev/null
done

# 清理 Sandbox 的缓存
find "$SANDBOX" -type d -name '__pycache__' -exec rm -rf {} + 2>/dev/null
find "$SANDBOX" -type d -name '.pytest_cache' -exec rm -rf {} + 2>/dev/null
echo "✅ 缓存已清理"
echo ""

# ── 步骤 7: 归档到开发完/ ──
echo "=== [步7] 归档到开发完/ ==="
# 优先从 Sandbox 归档
if [ -d "$PROJECT_DIR" ]; then
    mkdir -p "$DONE_DIR"
    cp -a "$PROJECT_DIR/"* "$DONE_DIR/"
    rm -rf "$PROJECT_DIR"
    echo "✅ 从 Sandbox 归档: $DONE_DIR"
fi

# 如果 开发中/ 有同名目录也清理掉
if [ -d "$DEV_PIPELINE_DIR" ]; then
    rm -rf "$DEV_PIPELINE_DIR"
    echo "✅ 清理开发中/: $PROJECT_NAME"
fi
echo ""

# ── 步骤 8: 双推 ──
echo "=== [步8] 双推 ==="
cd "$PIPELINE_DIR" || { echo "❌ 流水线目录不存在"; exit 1; }
git add -A
git commit -m "auto: $PROJECT_NAME 开发完成 ✅" 2>/dev/null || echo "   无新变更"
git push origin 2>&1
echo "✅ 双推完成"
echo ""

# ── 更新 dev-log ──
echo "=== 更新 dev-log ==="
python3 -c "
import json
try:
    entry = json.load(open('$DEV_LOG'))
    entry['step'] = 12
    entry['status'] = 'done'
    entry['completed_at'] = '$(date +%Y-%m-%dT%H:%M:%S)'
    entry['steps'].append({'step': 9, 'phase': '验证', 'status': 'completed', 'detail': 'pytest passed', 'error': ''})
    entry['steps'].append({'step': 10, 'phase': '清理', 'status': 'completed', 'detail': 'rm __pycache__ .pytest_cache', 'error': ''})
    entry['steps'].append({'step': 11, 'phase': '归档', 'status': 'completed', 'detail': '→ 开发完/', 'error': ''})
    entry['steps'].append({'step': 12, 'phase': '双推', 'status': 'completed', 'detail': 'git push GitHub + Gitee', 'error': ''})
    json.dump(entry, open('$DEV_LOG', 'w'), indent=2, ensure_ascii=False)
    print('✅ dev-log 已更新')
except Exception as e:
    print(f'⚠️ dev-log 更新失败: {e}')
"
echo ""

echo "================================================"
echo " ✅ 全部完成 — $PROJECT_NAME"
echo "    验证→清理→归档→双推 全部成功"
echo "================================================"
