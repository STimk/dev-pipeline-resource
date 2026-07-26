#!/usr/bin/env python3
"""
v5 动态难度分析 + 模型选择 + 验证策略

功能:
  1. 分析开发方案.md → 判断难度等级
  2. 动态分配模型（V4-Flash / V4-Pro）
  3. 判断是否需要视觉验证（OpenClaw + Kimi）
  4. 将配置写入 workspace task.md

难度等级:
  1 - 简单: 单一模块, 无 GUI, <5 功能点
  2 - 中等: 多模块, 文件IO, 5-10 功能点
  3 - 困难: 多模块, GUI/Web, 复杂算法, >10 功能点

模型分配:
  难度1: 编码 Flash, 测试 Flash
  难度2: 编码 Flash, 测试 Pro
  难度3: 编码 Pro,  测试 Pro

视觉验证:
  检测方案中是否包含 GUI/Web/界面/渲染 等关键词
  → 是: 启用 OpenClaw + Kimi 截图验证
  → 否: 仅 pytest 逻辑验证
"""

import re, json
from pathlib import Path

# ── GUI/视觉关键词 ──
GUI_KEYWORDS = [
    "gui", "web", "界面", "窗口", "渲染", "ui", "前端",
    "dashboard", "终端界面", "curses", "console ui",
    "图形", "图表", "chart", "display", "screen",
]

# ── 难度关键词权重 ──
DIFFICULTY_WEIGHTS = {
    # 功能复杂度
    "多线程": 2, "multithread": 2, "async": 2, "并发": 2,
    "数据库": 2, "database": 2, "sql": 2,
    "网络": 1, "network": 1, "api": 1, "http": 1,
    "算法": 2, "algorithm": 2, "搜索": 1, "排序": 1,
    "文件": 1, "file": 1, "io": 1,
    "配置": 1, "config": 1, "json": 1, "yaml": 1,

    # 模块数
    "模块": 0, "module": 0,
    "文件结构": 0, "目录": 0,

    # GUI
    "gui": 3, "web": 3, "界面": 2, "curses": 2,
    "窗口": 2, "渲染": 2,
}

def analyze_plan(plan_path: Path) -> dict:
    """
    分析方案.md → 返回难度/模型/视觉配置

    返回:
    {
        "difficulty": 1|2|3,
        "coding_model": "flash"|"pro",
        "testing_model": "flash"|"pro",
        "need_vision": True|False,
        "vision_reason": "",
        "feature_count": int,
        "module_count": int,
    }
    """
    content = plan_path.read_text(encoding="utf-8", errors="replace")
    text_lower = content.lower()

    # ── 统计功能点 ──
    feature_count = 0
    for line in content.splitlines():
        line = line.strip()
        # 检测 "- 功能" "1. 功能" "功能需求" 等
        if re.match(r'^[\d\-．•]\s*', line) and len(line) > 5:
            feature_count += 1
        if any(kw in line.lower() for kw in ["功能", "支持", "可实现"]):
            if not line.startswith("#") and not line.startswith("##"):
                pass  # 不重复计数

    # ── 统计模块数 ──
    module_count = 0
    in_file_section = False
    for line in content.splitlines():
        if re.match(r'^##?\s+(文件结构|目录|模块)', line):
            in_file_section = True
        if in_file_section and re.match(r'^├──|└──', line):
            if '.py' in line or '/' in line:
                module_count += 1

    # 兜底: 没有明确文件结构时估算
    if module_count == 0:
        module_count = max(1, feature_count // 3)

    # ── 计算难度分 ──
    score = 0
    for word, weight in DIFFICULTY_WEIGHTS.items():
        if word in text_lower:
            score += weight

    # 功能点数也影响难度
    if feature_count >= 10:
        score += 2
    elif feature_count >= 5:
        score += 1

    # ── 决定难度等级 ──
    if score >= 5:
        difficulty = 3  # 困难
    elif score >= 2:
        difficulty = 2  # 中等
    else:
        difficulty = 1  # 简单

    # ── 模型分配 ──
    model_map = {
        1: {"coding": "flash", "testing": "flash"},
        2: {"coding": "flash", "testing": "pro"},
        3: {"coding": "pro", "testing": "pro"},
    }
    models = model_map[difficulty]

    # ── 视觉验证判断 ──
    need_vision = False
    vision_reason = ""
    for kw in GUI_KEYWORDS:
        if kw in text_lower:
            need_vision = True
            vision_reason = f"方案包含 GUI 关键词: {kw}"
            break

    return {
        "difficulty": difficulty,
        "coding_model": models["coding"],
        "testing_model": models["testing"],
        "need_vision": need_vision,
        "vision_reason": vision_reason,
        "feature_count": feature_count,
        "module_count": module_count,
        "score": score,
    }


def generate_model_config(config: dict) -> str:
    """生成 task.md 可嵌入的模型配置块"""
    return f"""---
模型配置 (dev-collab-ultimate-v5 自动生成)
难度等级: {config['difficulty']} ({'简单' if config['difficulty']==1 else '中等' if config['difficulty']==2 else '困难'})
编码模型: V4-{'Flash' if config['coding_model']=='flash' else 'Pro'}
测试模型: V4-{'Flash' if config['testing_model']=='flash' else 'Pro'}
功能点数: {config['feature_count']}
模块数:   {config['module_count']}
视觉验证: {'是 - ' + config['vision_reason'] if config['need_vision'] else '否'}
---"""


def main():
    import sys
    if len(sys.argv) < 2:
        plan_path = Path("/mnt/f/AI_Work/Agent/Hermes/Sandbox/dev-pipeline/待开发")
        # 找最新的方案
        plans = sorted(plan_path.glob("*/开发方案.md"))
        if not plans:
            print("❌ 未找到方案")
            sys.exit(1)
        plan_path = plans[-1]
    else:
        plan_path = Path(sys.argv[1])

    if not plan_path.exists():
        print(f"❌ 方案不存在: {plan_path}")
        sys.exit(1)

    config = analyze_plan(plan_path)
    print(json.dumps(config, indent=2, ensure_ascii=False))
    print()
    print(generate_model_config(config))


if __name__ == "__main__":
    main()
