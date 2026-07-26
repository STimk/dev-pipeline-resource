#!/usr/bin/env python3
"""
pipeline-fix-loop.py — 自动修复回环模块

v5 核心: 当 pytest 失败时, Hermes 自动读取错误,
调用 Claude Code 修复, 重新验证, 最多 3 轮。

用法:
  python3 pipeline-fix-loop.py <项目目录> [--max-attempts 3]

流程:
  1. 运行 pytest → 捕获失败输出
  2. Hermes 分析错误 → 定位问题文件 + 行号
  3. 调用 Claude Code 修复（传入错误上下文）
  4. 重新 pytest
  5. 如果仍有失败 → 回到步骤 2
  6. 最多 N 轮
"""

import os, sys, json, subprocess, argparse, re
from pathlib import Path

SANDBOX = Path("/mnt/f/AI_Work/Agent/Hermes/Sandbox")
WORKSPACE = SANDBOX / ".workspace"
FIX_LOG = SANDBOX / ".workspace" / "fix-loop.json"


def run_pytest(project_dir: str) -> dict:
    """运行 pytest, 返回 {passed, output, failed_tests, errors}"""
    result = subprocess.run(
        ["python3", "-m", "pytest", "-v", "--tb=short"],
        cwd=project_dir,
        capture_output=True, text=True, timeout=120,
    )

    output = result.stdout + result.stderr
    failed_tests = []
    errors = []

    # 解析失败测试名
    for line in output.splitlines():
        if "FAILED" in line:
            failed_tests.append(line.strip())
        if "ERROR" in line and "test_" in line:
            errors.append(line.strip())

    return {
        "passed": result.returncode == 0,
        "exit_code": result.returncode,
        "output": output[-3000:],  # 保留最后 3000 字符
        "failed_tests": failed_tests,
        "errors": errors,
    }


def extract_error_context(pytest_output: str) -> str:
    """从 pytest 输出提取关键错误信息"""
    lines = pytest_output.splitlines()
    context_lines = []

    for i, line in enumerate(lines):
        # 捕获 FAILED / AssertionError / 异常类型
        if any(kw in line for kw in ["FAILED", "Error", "assert "]):
            # 取前后 3 行
            start = max(0, i - 3)
            end = min(len(lines), i + 4)
            context_lines.extend(lines[start:end])
            context_lines.append("---")

    return "\n".join(context_lines[-1500:])  # 最多 1500 字符


def call_claude_fix(error_context: str, project_dir: str):
    """把 pytest 错误喂给 Claude Code 修复"""
    fix_prompt = f"""
请修复以下 pytest 测试失败：

错误上下文:
{error_context}

项目目录: {project_dir}

要求:
1. 读取错误信息，定位到具体文件和行号
2. 修复代码中的 bug
3. 确保修复后 pytest 全部通过
4. 只修改必要的代码，不要重写整个文件
"""
    # 设置 DeepSeek 后端环境变量
    env = os.environ.copy()
    env["ANTHROPIC_BASE_URL"] = "https://api.deepseek.com/anthropic"
    # 从 credentials 读取 API key
    cred_file = Path.home() / ".config" / "opencode" / "credentials.sh"
    if cred_file.exists():
        for line in cred_file.read_text().splitlines():
            if "DEEPSEEK_API_KEY" in line:
                key = line.split("=", 1)[-1].strip().strip("'\"")
                env["ANTHROPIC_API_KEY"] = key
                break

    try:
        subprocess.run(
            ["/home/zhang/.local/bin/claude", "-p", fix_prompt,
             "--dangerously-skip-permissions", "--max-turns", "15"],
            cwd=project_dir, timeout=180, env=env,
        )
        return True
    except subprocess.TimeoutExpired:
        print("⚠️ Claude Code 超时")
        return False
    except FileNotFoundError:
        print("⚠️ Claude Code 未安装")
        return False


def fix_loop(project_dir: str, max_attempts: int = 3) -> dict:
    """自动修复回环主逻辑"""
    loop_log = {
        "project": Path(project_dir).name,
        "attempts": [],
        "final_status": "unknown",
    }

    for attempt in range(1, max_attempts + 1):
        print(f"\n{'='*50}")
        print(f"🔧 修复回环 第 {attempt}/{max_attempts} 轮")
        print(f"{'='*50}")

        # 跑 pytest
        result = run_pytest(project_dir)
        passed = result["passed"]
        failed_count = len(result["failed_tests"])

        print(f"  测试: {'✅ 通过' if passed else f'❌ {failed_count} 个失败'}")

        # 记录本轮
        attempt_log = {
            "attempt": attempt,
            "passed": passed,
            "failed_tests": result["failed_tests"][:10],
            "exit_code": result["exit_code"],
        }
        loop_log["attempts"].append(attempt_log)

        if passed:
            loop_log["final_status"] = "passed"
            break

        # 提取错误上下文
        error_ctx = extract_error_context(result["output"])
        print(f"  错误上下文 ({len(error_ctx)} chars)")
        print(f"  {result['failed_tests'][:5]}")

        # 调用 Claude Code 修复
        print(f"  🔄 调用 Claude Code 修复...")
        success = call_claude_fix(error_ctx, project_dir)
        print(f"  修复调用: {'✅' if success else '❌'}")

        if attempt == max_attempts:
            loop_log["final_status"] = "failed"

    # 保存修复日志
    FIX_LOG.parent.mkdir(parents=True, exist_ok=True)
    FIX_LOG.write_text(json.dumps(loop_log, indent=2, ensure_ascii=False))
    print(f"\n📋 修复日志: {FIX_LOG}")

    return loop_log


def main():
    parser = argparse.ArgumentParser(description="自动修复回环")
    parser.add_argument("project_dir", help="项目目录")
    parser.add_argument("--max-attempts", type=int, default=3)
    args = parser.parse_args()

    result = fix_loop(args.project_dir, args.max_attempts)
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
