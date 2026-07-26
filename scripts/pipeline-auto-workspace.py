#!/usr/bin/env python3
"""
自动从开发方案.md 生成 workspace 文件 (MANIFEST.md + 3 task.md)
不需要 Hermes 参与，由 monitor 守护进程自动触发。

用法:
  python3 pipeline-auto-workspace.py <项目目录路径>

流程:
  1. 读取开发方案.md → 提取项目名和技术栈
  2. 生成 MANIFEST.md（项目结构）
  3. 生成 claude_task.md（编码任务 + step_3_done）
  4. 生成 opencode_task.md（测试任务 + step_4_done）
"""

import os, sys, re
from pathlib import Path
from datetime import datetime

SANDBOX = Path("/mnt/f/AI_Work/Agent/Hermes/Sandbox")
WORKSPACE = SANDBOX / ".workspace"

def extract_project_name(plan_path):
    """从方案目录名获取完整项目名 (YYYY-MM-DD-项目名)"""
    return plan_path.parent.name  # 直接用目录名，如 "2026-07-26-消消乐"

def extract_description(plan_path):
    """提取方案的第一段描述"""
    content = plan_path.read_text(encoding="utf-8", errors="replace")
    lines = content.splitlines()
    desc_lines = []
    in_desc = False
    for line in lines:
        if line.strip().startswith("## ") and in_desc:
            break
        if line.strip().startswith("# ") and not line.strip().startswith("# 开发方案"):
            in_desc = True
            continue
        if in_desc and line.strip():
            desc_lines.append(line.strip())
            if len(desc_lines) >= 3:
                break
    return "\n".join(desc_lines) if desc_lines else "无描述"

def extract_tech_stack(plan_path):
    """提取技术栈"""
    content = plan_path.read_text(encoding="utf-8", errors="replace")
    lines = content.splitlines()
    in_tech = False
    techs = []
    for line in lines:
        if line.strip().startswith("## 技术栈"):
            in_tech = True
            continue
        if in_tech and line.strip().startswith("## "):
            break
        if in_tech and line.strip():
            techs.append(line.strip().lstrip("- "))
    return techs

def generate_manifest(project_name, description, techs):
    return f"""# MANIFEST — {project_name}

## 概述
{description}

## 技术栈
{chr(10).join(f'- {t}' for t in techs) if techs else '- Python 3.12'}

## 项目结构
```
{project_name}/
├── src/                  # 源代码
│   └── __init__.py
├── tests/               # 测试
│   └── __init__.py
├── setup.py             # 安装配置
├── pyproject.toml       # 项目元数据
└── README.md
```

## 开发流程
1. Claude Code → 写全部代码
2. OpenCode → 写 pytest 测试
3. Ultimate → 验证→清理→归档→双推
"""

def generate_claude_task(project_name, plan_path):
    plan_content = plan_path.read_text(encoding="utf-8", errors="replace")
    return f"""# Claude Code 任务 — 编码

## 项目
{project_name}

## 开发方案
```
{plan_content[:3000]}
```

## 任务要求
1. 读取上方开发方案，理解全部功能需求
2. 在 /mnt/f/AI_Work/Agent/Hermes/Sandbox/{project_name}/ 下创建完整项目
3. 包括: 源代码、配置文件、示例文件
4. 代码质量: 函数有类型注解，有 docstring，异常处理完整
5. 全部完成后，在文件末尾另起一行写入完成标记（标记内容是 ✅ step_3_done）

（注意: 不要删除或修改已有的"完成标记"段落，在末尾另起一行追加）
"""

def generate_opencode_task(project_name):
    return f"""# OpenCode 任务 — 测试

## 项目
{project_name}

## 任务要求
1. 确认 /mnt/f/AI_Work/Agent/Hermes/Sandbox/{project_name}/ 下已有代码
2. 写 pytest 测试，覆盖全部核心功能
3. 测试必须全部通过
4. 全部完成后，在文件末尾另起一行写入完成标记（标记内容是 ✅ step_4_done）

（注意: 不要删除或修改已有的"完成标记"段落，在末尾另起一行追加）

"""

def main():
    if len(sys.argv) < 2:
        print("用法: pipeline-auto-workspace.py <方案.md路径>")
        sys.exit(1)
    
    plan_path = Path(sys.argv[1])
    if not plan_path.exists():
        print(f"❌ 方案不存在: {plan_path}")
        sys.exit(1)
    
    project_name = extract_project_name(plan_path)
    description = extract_description(plan_path)
    techs = extract_tech_stack(plan_path)
    
    # 创建 workspace 目录
    WORKSPACE.mkdir(parents=True, exist_ok=True)
    
    # 写 MANIFEST.md
    manifest = generate_manifest(project_name, description, techs)
    (WORKSPACE / "MANIFEST.md").write_text(manifest, encoding="utf-8")
    print(f"✅ MANIFEST.md → {project_name}")
    
    # 写 claude_task.md
    claude_task = generate_claude_task(project_name, plan_path)
    (WORKSPACE / "claude_task.md").write_text(claude_task, encoding="utf-8")
    print(f"✅ claude_task.md (编码 → 追加 step_3_done)")
    
    # 写 opencode_task.md
    opencode_task = generate_opencode_task(project_name)
    (WORKSPACE / "opencode_task.md").write_text(opencode_task, encoding="utf-8")
    print(f"✅ opencode_task.md (测试 → 追加 step_4_done)")
    
    print(f"\n📋 workspace 就绪: {WORKSPACE}/")
    print(f"🚀 可以启动 3 个 WT 标签了")

if __name__ == "__main__":
    main()
